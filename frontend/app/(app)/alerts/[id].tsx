import { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  ActivityIndicator,
} from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as Haptics from "expo-haptics";

import { apiFetch, Alert } from "@/src/api/client";
import { colors, spacing, radius } from "@/src/theme";

export default function AlertDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [alert, setAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const a = await apiFetch<Alert>(`/alerts/${id}`);
      setAlert(a);
    } catch (e) {
      console.log("alert detail error", e);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const resolve = async () => {
    if (!alert || alert.resolved) return;
    setResolving(true);
    try {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      const updated = await apiFetch<Alert>(`/alerts/${alert.id}/resolve`, {
        method: "POST",
      });
      setAlert(updated);
    } catch (e) {
      console.log("resolve error", e);
    } finally {
      setResolving(false);
    }
  };

  if (loading || !alert) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator color={colors.brandPrimary} />
        </View>
      </SafeAreaView>
    );
  }

  const sevColor =
    alert.severity === "error" ? colors.error : colors.warning;

  const imgSrc: any = alert.image_base64
    ? { uri: `data:image/jpeg;base64,${alert.image_base64}` }
    : alert.image_url || null;

  return (
    <View style={{ flex: 1, backgroundColor: colors.surface }} testID="alert-detail-screen">
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ paddingBottom: 120 }}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.hero}>
          {imgSrc ? (
            <Image
              source={imgSrc}
              style={StyleSheet.absoluteFillObject}
              contentFit="cover"
            />
          ) : (
            <View
              style={[
                StyleSheet.absoluteFillObject,
                { backgroundColor: colors.surfaceTertiary },
              ]}
            />
          )}
          <LinearGradient
            colors={[
              "rgba(0,0,0,0.45)",
              "rgba(0,0,0,0.05)",
              "rgba(0,0,0,0.55)",
            ]}
            style={StyleSheet.absoluteFillObject}
          />
          <SafeAreaView edges={["top"]} style={styles.heroSafe}>
            <View style={styles.heroTop}>
              <Pressable
                testID="alert-back-button"
                onPress={() => router.back()}
                style={styles.backBtn}
              >
                <Ionicons name="chevron-back" size={22} color={colors.onSurface} />
              </Pressable>
              <View style={styles.confPill}>
                <Ionicons name="scan" size={12} color={colors.brand} />
                <Text style={styles.confText}>
                  {Math.round(alert.confidence * 100)}% de Precisão
                </Text>
              </View>
            </View>
            <View style={styles.heroBottom}>
              <View style={[styles.sevChip, { backgroundColor: sevColor }]}>
                <Ionicons
                  name={alert.severity === "error" ? "alert" : "warning"}
                  size={12}
                  color="#fff"
                />
                <Text style={styles.sevText}>
                  {alert.severity === "error" ? "Alta severidade" : "Atenção"}
                </Text>
              </View>
              <Text style={styles.heroTitle}>{alert.disease}</Text>
              <Text style={styles.heroZone}>
                {alert.plant_zone || "Zona não informada"}
              </Text>
            </View>
          </SafeAreaView>
        </View>

        {/* Content */}
        <View style={styles.content}>
          <Section title="Descrição da Detecção">
            <Text style={styles.body}>
              {alert.description ||
                "A visão computacional identificou uma anomalia consistente com a doença acima. Verifique as plantas na zona indicada."}
            </Text>
          </Section>

          <Section title="Recomendações de Ação">
            {(alert.recommendations || []).length === 0 ? (
              <Text style={styles.body}>
                Nenhuma recomendação específica foi fornecida.
              </Text>
            ) : (
              (alert.recommendations || []).map((r, i) => (
                <View key={i} style={styles.recRow}>
                  <View style={styles.recDot}>
                    <Ionicons
                      name="checkmark"
                      size={12}
                      color={colors.onBrandPrimary}
                    />
                  </View>
                  <Text style={styles.recText}>{r}</Text>
                </View>
              ))
            )}
          </Section>

          <Section title="Detectado em">
            <Text style={styles.body}>{new Date(alert.created_at).toLocaleString("pt-BR")}</Text>
          </Section>
        </View>
      </ScrollView>

      {/* Sticky CTA */}
      <SafeAreaView edges={["bottom"]} style={styles.ctaBar}>
        <Pressable
          testID="resolve-alert-button"
          onPress={resolve}
          disabled={alert.resolved || resolving}
          style={({ pressed }) => [
            styles.cta,
            (alert.resolved || resolving) && { opacity: 0.7 },
            pressed && !alert.resolved && { opacity: 0.85 },
            alert.resolved && { backgroundColor: colors.success },
          ]}
        >
          {resolving ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Ionicons
                name={alert.resolved ? "checkmark-circle" : "checkmark-done"}
                size={18}
                color="#fff"
              />
              <Text style={styles.ctaText}>
                {alert.resolved ? "Resolvido" : "Marcar como Resolvido"}
              </Text>
            </>
          )}
        </Pressable>
      </SafeAreaView>
    </View>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <View style={{ marginTop: spacing.xl }}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={{ marginTop: spacing.sm }}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.surface },
  hero: { height: 340, width: "100%" },
  heroSafe: {
    flex: 1,
    paddingHorizontal: spacing.xl,
    justifyContent: "space-between",
    paddingBottom: spacing.lg,
  },
  heroTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: spacing.xs,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    backgroundColor: "rgba(255,255,255,0.92)",
    alignItems: "center",
    justifyContent: "center",
  },
  confPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: radius.pill,
    backgroundColor: "rgba(234,242,237,0.95)",
  },
  confText: {
    color: colors.brand,
    fontWeight: "700",
    fontSize: 12,
  },
  heroBottom: { gap: spacing.sm },
  sevChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: radius.pill,
    alignSelf: "flex-start",
  },
  sevText: {
    color: "#fff",
    fontSize: 11,
    fontWeight: "700",
  },
  heroTitle: {
    color: "#fff",
    fontSize: 26,
    fontWeight: "700",
    letterSpacing: -0.5,
  },
  heroZone: {
    color: "#fff",
    opacity: 0.9,
    fontSize: 13,
  },
  content: { paddingHorizontal: spacing.xl },
  sectionTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  body: {
    fontSize: 14.5,
    color: colors.onSurface,
    lineHeight: 22,
  },
  recRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  recDot: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.brandPrimary,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
  },
  recText: { flex: 1, fontSize: 14, color: colors.onSurface, lineHeight: 21 },
  ctaBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.md,
    backgroundColor: colors.surface,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  cta: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: colors.brandPrimary,
    height: 52,
    borderRadius: radius.md,
  },
  ctaText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "700",
  },
});
