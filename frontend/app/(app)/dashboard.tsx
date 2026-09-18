import { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Pressable,
  ActivityIndicator,
} from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";

import { apiFetch, SensorReading, Alert } from "@/src/api/client";
import { useAuth } from "@/src/context/auth";
import { colors, spacing, radius } from "@/src/theme";

const HERO_BG =
  "https://images.pexels.com/photos/89267/pexels-photo-89267.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940";

type Metric = {
  key: keyof SensorReading;
  label: string;
  unit: string;
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
  ideal: [number, number];
};

const METRICS: Metric[] = [
  {
    key: "Temperatura",
    label: "Temperatura",
    unit: "°C",
    icon: "thermometer-outline",
    tint: "#E85D3D",
    ideal: [18, 25],
  },
  {
    key: "Umidade",
    label: "Umidade do Ar",
    unit: "%",
    icon: "water-outline",
    tint: "#2E7CD6",
    ideal: [55, 75],
  },
];

function statusOf(v: number | undefined | null, ideal: [number, number]) {
  if (v === undefined || v === null) return { label: "—", color: colors.muted };
  if (v < ideal[0]) return { label: "Baixo", color: colors.warning };
  if (v > ideal[1]) return { label: "Alto", color: colors.error };
  return { label: "Ideal", color: colors.success };
}

function formatFullDateTime(iso: string) {
  try {
    const d = new Date(iso);
    const dateStr = d.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
    const timeStr = d.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    return `${dateStr} às ${timeStr}`;
  } catch {
    return "—";
  }
}

function formatTime(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export default function Dashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const [reading, setReading] = useState<SensorReading | null>(null);
  const [unread, setUnread] = useState<number>(0);
  const [recent, setRecent] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await apiFetch<SensorReading | null>("/sensors/latest");
      setReading(r);

      try {
        const alerts = await apiFetch<Alert[]>("/alerts");
        const count = await apiFetch<{ count: number }>("/alerts/unread-count");
        setRecent(alerts.slice(0, 3));
        setUnread(count.count);
      } catch {
        setRecent([]);
        setUnread(0);
      }
    } catch (e) {
      console.log("load error", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load]);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const healthy = unread === 0;

  return (
    <SafeAreaView
      style={styles.safe}
      edges={["top", "left", "right"]}
      testID="dashboard-screen"
    >
      <ScrollView
        contentContainerStyle={{ paddingBottom: spacing.xxxl }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.brandPrimary} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.hello}>Olá,</Text>
            <Text style={styles.name}>{user?.Nome || "Produtor"}</Text>
          </View>
          <Pressable
            testID="dashboard-alerts-button"
            onPress={() => router.push("/(app)/alerts")}
            style={styles.bellBtn}
          >
            <Ionicons
              name="notifications-outline"
              size={22}
              color={colors.onSurface}
            />
            {unread > 0 && (
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{unread}</Text>
              </View>
            )}
          </Pressable>
        </View>

        {/* Hero status card */}
        <View style={styles.heroCard}>
          <Image
            source={HERO_BG}
            style={StyleSheet.absoluteFill}
            contentFit="cover"
          />
          <LinearGradient
            colors={["rgba(10,76,54,0.55)", "rgba(10,76,54,0.85)"]}
            style={StyleSheet.absoluteFill}
          />
          <View style={styles.heroInner}>
            <View style={styles.heroTopRow}>
              <View
                style={[
                  styles.heroStatusPill,
                  {
                    backgroundColor: healthy
                      ? "rgba(216,230,222,0.9)"
                      : "rgba(200,76,49,0.9)",
                  },
                ]}
              >
                <Ionicons
                  name={healthy ? "checkmark-circle" : "warning"}
                  size={14}
                  color={healthy ? colors.brand : "#fff"}
                />
                <Text
                  style={[
                    styles.heroStatusText,
                    { color: healthy ? colors.brand : "#fff" },
                  ]}
                >
                  {healthy ? "Safra Saudável" : `${unread} alerta${unread > 1 ? "s" : ""}`}
                </Text>
              </View>
              <Text style={styles.heroTime}>
                {reading ? `atualizado ${formatTime(reading.DataHoraEnvio)}` : ""}
              </Text>
            </View>
            <Text style={styles.heroTitle}>Estufa Alface</Text>
            <Text style={styles.heroSubtitle}>
              {healthy
                ? "Todos os sensores dentro do ideal."
                : "Detecções de doença requerem sua atenção."}
            </Text>
          </View>
        </View>

        {/* Sensor grid */}
        <View style={styles.sectionRow}>
          <Text style={styles.sectionTitle}>Sensores</Text>
          <Text style={styles.sectionHint}>
            {reading ? `há ${timeAgo(reading.DataHoraEnvio)}` : "—"}
          </Text>
        </View>

        {/* Card do Último Envio do Sensor */}
        {reading && (
          <View style={styles.lastSendCard}>
            <Ionicons name="time-outline" size={18} color={colors.brandPrimary} />
            <View style={{ flex: 1 }}>
              <Text style={styles.lastSendLabel}>Último Envio de Telemetria</Text>
              <Text style={styles.lastSendValue}>
                {formatFullDateTime(reading.DataHoraEnvio)}
              </Text>
            </View>
            <Text style={styles.deviceIdBadge}>{reading.DeviceId || "ESP32"}</Text>
          </View>
        )}

        {loading ? (
          <View style={{ padding: spacing.xl }}>
            <ActivityIndicator color={colors.brandPrimary} />
          </View>
        ) : reading ? (
          <View style={styles.grid}>
            {METRICS.map((m) => {
              const v = reading[m.key] as number | undefined | null;
              const s = statusOf(v, m.ideal);
              return (
                <View
                  key={m.key}
                  testID={`metric-${m.key}`}
                  style={styles.metricCard}
                >
                  <View
                    style={[
                      styles.metricIconWrap,
                      { backgroundColor: colors.brandTertiary },
                    ]}
                  >
                    <Ionicons name={m.icon} size={18} color={m.tint} />
                  </View>
                  <Text style={styles.metricLabel}>{m.label}</Text>
                  <View style={styles.metricValueRow}>
                    <Text style={styles.metricValue}>
                      {typeof v === "number" ? v.toFixed(1) : "—"}
                    </Text>
                    <Text style={styles.metricUnit}>{m.unit}</Text>
                  </View>
                  <View
                    style={[
                      styles.metricStatus,
                      { backgroundColor: s.color + "22" },
                    ]}
                  >
                    <View
                      style={[styles.metricDot, { backgroundColor: s.color }]}
                    />
                    <Text style={[styles.metricStatusText, { color: s.color }]}>
                      {s.label}
                    </Text>
                  </View>
                </View>
              );
            })}
          </View>
        ) : (
          <View style={styles.empty}>
            <Ionicons name="cloud-offline-outline" size={32} color={colors.muted} />
            <Text style={styles.emptyText}>Nenhum sensor conectado.</Text>
          </View>
        )}

        {/* Recent alerts */}
        <View style={styles.sectionRow}>
          <Text style={styles.sectionTitle}>Alertas Recentes</Text>
          <Pressable onPress={() => router.push("/(app)/alerts")}>
            <Text style={styles.link}>Ver todos</Text>
          </Pressable>
        </View>

        {recent.length === 0 ? (
          <View style={styles.empty}>
            <Ionicons name="shield-checkmark-outline" size={32} color={colors.brandPrimary} />
            <Text style={styles.emptyText}>Sua estufa está segura.</Text>
          </View>
        ) : (
          recent.map((a) => (
            <Pressable
              key={a.id}
              testID={`recent-alert-${a.id}`}
              style={styles.alertRow}
              onPress={() => router.push(`/(app)/alerts/${a.id}`)}
            >
              <View
                style={[
                  styles.alertIconWrap,
                  {
                    backgroundColor:
                      a.severity === "error"
                        ? colors.error + "22"
                        : colors.warning + "22",
                  },
                ]}
              >
                <Ionicons
                  name="alert-circle"
                  size={20}
                  color={a.severity === "error" ? colors.error : colors.warning}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.alertTitle} numberOfLines={1}>
                  {a.disease}
                </Text>
                <Text style={styles.alertSub} numberOfLines={1}>
                  {a.plant_zone || "Zona não informada"} · {Math.round(a.confidence * 100)}%
                </Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={colors.muted} />
            </Pressable>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function timeAgo(iso: string) {
  const d = new Date(iso).getTime();
  const diff = Math.max(0, Date.now() - d);
  const min = Math.round(diff / 60000);
  if (min < 1) return "agora";
  if (min < 60) return `${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `${h} h`;
  return `${Math.round(h / 24)} d`;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.surface },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
  },
  hello: { fontSize: 13, color: colors.muted },
  name: {
    fontSize: 20,
    fontWeight: "700",
    color: colors.onSurface,
    letterSpacing: -0.3,
  },
  bellBtn: {
    width: 42,
    height: 42,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceSecondary,
    alignItems: "center",
    justifyContent: "center",
  },
  badge: {
    position: "absolute",
    top: 4,
    right: 4,
    minWidth: 18,
    height: 18,
    paddingHorizontal: 4,
    borderRadius: 9,
    backgroundColor: colors.error,
    alignItems: "center",
    justifyContent: "center",
  },
  badgeText: {
    color: "#fff",
    fontSize: 10,
    fontWeight: "700",
  },
  heroCard: {
    marginHorizontal: spacing.xl,
    height: 160,
    borderRadius: radius.lg,
    overflow: "hidden",
  },
  heroInner: {
    flex: 1,
    padding: spacing.lg,
    justifyContent: "space-between",
  },
  heroTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  heroStatusPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: radius.pill,
  },
  heroStatusText: { fontSize: 12, fontWeight: "700" },
  heroTime: {
    color: "#fff",
    fontSize: 11,
    opacity: 0.85,
  },
  heroTitle: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "700",
    letterSpacing: -0.3,
  },
  heroSubtitle: {
    color: "#fff",
    opacity: 0.85,
    fontSize: 13,
  },
  sectionRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    paddingHorizontal: spacing.xl,
    marginTop: spacing.xl,
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.onSurface,
    letterSpacing: -0.2,
  },
  sectionHint: { fontSize: 12, color: colors.muted },
  lastSendCard: {
    flexDirection: "row",
    alignItems: "center",
    marginHorizontal: spacing.xl,
    marginBottom: spacing.md,
    padding: spacing.md,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: radius.md,
    gap: spacing.sm,
  },
  lastSendLabel: {
    fontSize: 11,
    color: colors.muted,
  },
  lastSendValue: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.onSurface,
    marginTop: 2,
  },
  deviceIdBadge: {
    fontSize: 10,
    fontWeight: "700",
    color: colors.brandPrimary,
    backgroundColor: colors.brandTertiary,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radius.pill,
  },
  link: { color: colors.brandPrimary, fontSize: 13, fontWeight: "600" },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingHorizontal: spacing.xl - spacing.xs,
  },
  metricCard: {
    width: "50%",
    padding: spacing.xs,
  },
  metricIconWrap: {
    width: 36,
    height: 36,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.sm,
  },
  metricLabel: {
    fontSize: 12,
    color: colors.muted,
    marginBottom: 2,
  },
  metricValueRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 4,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: "700",
    color: colors.onSurface,
    letterSpacing: -0.5,
  },
  metricUnit: { fontSize: 12, color: colors.muted, fontWeight: "500" },
  metricStatus: {
    marginTop: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    alignSelf: "flex-start",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radius.pill,
  },
  metricDot: { width: 6, height: 6, borderRadius: 3 },
  metricStatusText: { fontSize: 11, fontWeight: "700" },
  empty: {
    marginHorizontal: spacing.xl,
    padding: spacing.xl,
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: radius.md,
  },
  emptyText: { color: colors.muted, fontSize: 13 },
  alertRow: {
    flexDirection: "row",
    alignItems: "center",
    marginHorizontal: spacing.xl,
    marginBottom: spacing.sm,
    padding: spacing.md,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: radius.md,
    gap: spacing.md,
  },
  alertIconWrap: {
    width: 40,
    height: 40,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
  },
  alertTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: colors.onSurface,
  },
  alertSub: {
    marginTop: 2,
    fontSize: 12,
    color: colors.muted,
  },
});