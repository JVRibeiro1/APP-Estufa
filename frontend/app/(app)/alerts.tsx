import { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Pressable,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { Image } from "expo-image";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter, useFocusEffect } from "expo-router";

import { apiFetch, Alert } from "@/src/api/client";
import { colors, spacing, radius } from "@/src/theme";

type Filter = "all" | "unread";

export default function AlertsScreen() {
  const router = useRouter();
  const [items, setItems] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");

  const load = useCallback(async () => {
    try {
      const r = await apiFetch<Alert[]>(
        `/alerts${filter === "unread" ? "?unread_only=true" : ""}`
      );
      setItems(r);
    } catch (e) {
      console.log("alerts load error", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return (
    <SafeAreaView
      style={styles.safe}
      edges={["top", "left", "right"]}
      testID="alerts-screen"
    >
      <View style={styles.header}>
        <Text style={styles.title}>Alertas</Text>
        <Text style={styles.subtitle}>
          Detecções da visão computacional
        </Text>
      </View>

      <View style={styles.segment}>
        <SegBtn
          label="Todos"
          active={filter === "all"}
          onPress={() => setFilter("all")}
          testID="filter-all"
        />
        <SegBtn
          label="Não lidos"
          active={filter === "unread"}
          onPress={() => setFilter("unread")}
          testID="filter-unread"
        />
      </View>

      {loading ? (
        <View style={{ padding: spacing.xxl, alignItems: "center" }}>
          <ActivityIndicator color={colors.brandPrimary} />
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(i) => i.id}
          contentContainerStyle={{
            paddingHorizontal: spacing.xl,
            paddingBottom: spacing.xxxl,
          }}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => {
                setRefreshing(true);
                load();
              }}
              tintColor={colors.brandPrimary}
            />
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Ionicons
                name="shield-checkmark-outline"
                size={40}
                color={colors.brandPrimary}
              />
              <Text style={styles.emptyTitle}>Estufa segura</Text>
              <Text style={styles.emptySub}>
                Nenhuma doença detectada. Sua safra está saudável.
              </Text>
            </View>
          }
          renderItem={({ item }) => (
            <Pressable
              testID={`alert-row-${item.id}`}
              style={[styles.row, item.resolved && { opacity: 0.55 }]}
              onPress={() => router.push(`/(app)/alerts/${item.id}`)}
            >
              {item.image_url || item.image_base64 ? (
                <Image
                  source={
                    item.image_base64
                      ? { uri: `data:image/jpeg;base64,${item.image_base64}` }
                      : item.image_url!
                  }
                  style={styles.thumb}
                  contentFit="cover"
                />
              ) : (
                <View
                  style={[
                    styles.thumb,
                    {
                      backgroundColor:
                        item.severity === "error"
                          ? colors.error + "22"
                          : colors.warning + "22",
                      alignItems: "center",
                      justifyContent: "center",
                    },
                  ]}
                >
                  <Ionicons
                    name="leaf"
                    size={22}
                    color={
                      item.severity === "error" ? colors.error : colors.warning
                    }
                  />
                </View>
              )}
              <View style={{ flex: 1 }}>
                <View style={styles.rowTop}>
                  <Text style={styles.rowTitle} numberOfLines={1}>
                    {item.disease}
                  </Text>
                  {!item.read && !item.resolved && (
                    <View
                      style={[
                        styles.unreadDot,
                        {
                          backgroundColor:
                            item.severity === "error"
                              ? colors.error
                              : colors.warning,
                        },
                      ]}
                    />
                  )}
                </View>
                <Text style={styles.rowSub} numberOfLines={1}>
                  {item.plant_zone || "Zona não informada"}
                </Text>
                <View style={styles.rowMeta}>
                  <View style={styles.confPill}>
                    <Text style={styles.confText}>
                      {Math.round(item.confidence * 100)}%
                    </Text>
                  </View>
                  <Text style={styles.timeText}>
                    {timeAgo(item.created_at)}
                  </Text>
                  {item.resolved && (
                    <View style={styles.resolvedPill}>
                      <Ionicons
                        name="checkmark"
                        size={11}
                        color={colors.success}
                      />
                      <Text style={styles.resolvedText}>Resolvido</Text>
                    </View>
                  )}
                </View>
              </View>
              <Ionicons name="chevron-forward" size={18} color={colors.muted} />
            </Pressable>
          )}
        />
      )}
    </SafeAreaView>
  );
}

function SegBtn({
  label,
  active,
  onPress,
  testID,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  testID: string;
}) {
  return (
    <Pressable
      testID={testID}
      onPress={onPress}
      style={[styles.segBtn, active && styles.segBtnActive]}
    >
      <Text style={[styles.segText, active && styles.segTextActive]}>
        {label}
      </Text>
    </Pressable>
  );
}

function timeAgo(iso: string) {
  const d = new Date(iso).getTime();
  const diff = Math.max(0, Date.now() - d);
  const min = Math.round(diff / 60000);
  if (min < 1) return "agora";
  if (min < 60) return `há ${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `há ${h} h`;
  return `há ${Math.round(h / 24)} d`;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.surface },
  header: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: colors.onSurface,
    letterSpacing: -0.5,
  },
  subtitle: {
    marginTop: 2,
    fontSize: 13,
    color: colors.muted,
  },
  segment: {
    flexDirection: "row",
    marginHorizontal: spacing.xl,
    padding: 4,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: radius.pill,
    marginBottom: spacing.md,
  },
  segBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    borderRadius: radius.pill,
  },
  segBtnActive: { backgroundColor: colors.surface },
  segText: { fontSize: 13, color: colors.muted, fontWeight: "600" },
  segTextActive: { color: colors.brand },
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.divider,
    gap: spacing.md,
  },
  thumb: {
    width: 56,
    height: 56,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceSecondary,
  },
  rowTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  rowTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: colors.onSurface,
    flex: 1,
  },
  unreadDot: { width: 8, height: 8, borderRadius: 4 },
  rowSub: { marginTop: 2, fontSize: 12, color: colors.muted },
  rowMeta: {
    marginTop: 6,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  confPill: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radius.pill,
    backgroundColor: colors.brandTertiary,
  },
  confText: {
    fontSize: 11,
    fontWeight: "700",
    color: colors.brand,
  },
  timeText: { fontSize: 11, color: colors.muted },
  resolvedPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: radius.pill,
    backgroundColor: colors.success + "22",
  },
  resolvedText: {
    fontSize: 10,
    fontWeight: "700",
    color: colors.success,
  },
  empty: {
    padding: spacing.xxl,
    alignItems: "center",
    gap: spacing.sm,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: colors.onSurface,
    marginTop: spacing.sm,
  },
  emptySub: {
    fontSize: 13,
    color: colors.muted,
    textAlign: "center",
  },
});
