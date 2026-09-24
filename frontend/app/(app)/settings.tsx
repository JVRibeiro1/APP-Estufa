import { View, Text, StyleSheet, Pressable, ScrollView } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "@/src/context/auth";
import { colors, spacing, radius } from "@/src/theme";

export default function Settings() {
  const { user, signOut } = useAuth();

  return (
    <SafeAreaView style={styles.safe} edges={["top", "left", "right"]} testID="settings-screen">
      <ScrollView contentContainerStyle={{ paddingBottom: spacing.xxxl }}>
        <View style={styles.header}>
          <Text style={styles.title}>Perfil</Text>
        </View>

        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={26} color={colors.onBrandPrimary} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.profileName}>{user?.name || "Produtor"}</Text>
            <Text style={styles.profileEmail}>{user?.email}</Text>
          </View>
        </View>

        <SectionTitle>Preferências</SectionTitle>

        <Row
          icon="notifications-outline"
          label="Notificações"
          hint="Ativas no dispositivo"
          testID="row-notifications"
        />
        <Row
          icon="cellular-outline"
          label="Sensores Conectados"
          hint="5 sensores"
          testID="row-sensors"
        />
        <Row
          icon="camera-outline"
          label="Visão Computacional"
          hint="API externa"
          testID="row-cv"
        />

        <SectionTitle>Sobre</SectionTitle>

        <Row
          icon="information-circle-outline"
          label="Versão"
          hint="1.0.0"
          testID="row-version"
        />
        <Row
          icon="shield-checkmark-outline"
          label="Privacidade & Termos"
          testID="row-privacy"
        />

        <Pressable
          testID="signout-button"
          onPress={signOut}
          style={({ pressed }) => [
            styles.signOut,
            pressed && { opacity: 0.85 },
          ]}
        >
          <Ionicons name="log-out-outline" size={18} color={colors.error} />
          <Text style={styles.signOutText}>Sair</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

function Row({
  icon,
  label,
  hint,
  testID,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  hint?: string;
  testID?: string;
}) {
  return (
    <Pressable testID={testID} style={({ pressed }) => [styles.row, pressed && { opacity: 0.7 }]}>
      <View style={styles.rowIcon}>
        <Ionicons name={icon} size={18} color={colors.brand} />
      </View>
      <Text style={styles.rowLabel}>{label}</Text>
      {hint && <Text style={styles.rowHint}>{hint}</Text>}
      <Ionicons name="chevron-forward" size={16} color={colors.muted} />
    </Pressable>
  );
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
  profileCard: {
    marginHorizontal: spacing.xl,
    marginTop: spacing.sm,
    padding: spacing.lg,
    borderRadius: radius.lg,
    backgroundColor: colors.surfaceSecondary,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: colors.brandPrimary,
    alignItems: "center",
    justifyContent: "center",
  },
  profileName: {
    fontSize: 17,
    fontWeight: "700",
    color: colors.onSurface,
  },
  profileEmail: {
    marginTop: 2,
    fontSize: 13,
    color: colors.muted,
  },
  sectionTitle: {
    marginTop: spacing.xl,
    marginBottom: spacing.sm,
    marginHorizontal: spacing.xl,
    fontSize: 12,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.divider,
    backgroundColor: colors.surface,
  },
  rowIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: colors.brandTertiary,
    alignItems: "center",
    justifyContent: "center",
  },
  rowLabel: {
    flex: 1,
    fontSize: 14.5,
    color: colors.onSurface,
    fontWeight: "500",
  },
  rowHint: { fontSize: 12.5, color: colors.muted, marginRight: spacing.xs },
  signOut: {
    marginHorizontal: spacing.xl,
    marginTop: spacing.xl,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    height: 50,
    borderRadius: radius.md,
    backgroundColor: colors.error + "15",
  },
  signOutText: {
    color: colors.error,
    fontSize: 15,
    fontWeight: "700",
  },
});
