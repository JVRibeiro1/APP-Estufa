import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Keyboard,
  TouchableWithoutFeedback,
  ActivityIndicator,
} from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";

import { useAuth } from "@/src/context/auth";
import { colors, spacing, radius } from "@/src/theme";

const HERO =
  "https://images.pexels.com/photos/37861016/pexels-photo-37861016.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940";

export default function Login() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("demo@estufa.com");
  const [password, setPassword] = useState("demo1234");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const onLogin = async () => {
    setErr(null);
    if (!email || !password) {
      setErr("Preencha e-mail e senha");
      return;
    }
    setLoading(true);
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      await signIn(email.trim(), password);
    } catch (e: any) {
      setErr(e.message || "Falha ao entrar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: colors.surface }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
        <ScrollView
          contentContainerStyle={{ flexGrow: 1 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.hero}>
            <Image
              source={HERO}
              style={StyleSheet.absoluteFillObject}
              contentFit="cover"
              transition={250}
            />
            <LinearGradient
              colors={["rgba(10,76,54,0.15)", "rgba(255,255,255,0)", colors.surface]}
              style={StyleSheet.absoluteFillObject}
            />
            <View style={styles.heroContent}>
              <View style={styles.logoPill}>
                <Ionicons name="leaf" size={16} color={colors.onBrandPrimary} />
                <Text style={styles.logoText}>AlfaceAI</Text>
              </View>
            </View>
          </View>

          <View style={styles.form}>
            <Text style={styles.title}>Bem-vindo à sua estufa</Text>
            <Text style={styles.subtitle}>
              Monitore sua safra e receba alertas de doenças em tempo real.
            </Text>

            <View style={{ marginTop: spacing.xl }}>
              <Text style={styles.label}>E-mail</Text>
              <View style={styles.inputWrap}>
                <Ionicons name="mail-outline" size={18} color={colors.muted} />
                <TextInput
                  testID="login-email-input"
                  value={email}
                  onChangeText={setEmail}
                  placeholder="voce@exemplo.com"
                  placeholderTextColor={colors.muted}
                  autoCapitalize="none"
                  keyboardType="email-address"
                  style={styles.input}
                />
              </View>
            </View>

            <View style={{ marginTop: spacing.lg }}>
              <Text style={styles.label}>Senha</Text>
              <View style={styles.inputWrap}>
                <Ionicons
                  name="lock-closed-outline"
                  size={18}
                  color={colors.muted}
                />
                <TextInput
                  testID="login-password-input"
                  value={password}
                  onChangeText={setPassword}
                  placeholder="Sua senha"
                  placeholderTextColor={colors.muted}
                  secureTextEntry
                  style={styles.input}
                />
              </View>
            </View>

            {err && (
              <Text testID="login-error" style={styles.error}>
                {err}
              </Text>
            )}

            <Pressable
              testID="login-submit-button"
              onPress={onLogin}
              disabled={loading}
              style={({ pressed }) => [
                styles.btn,
                pressed && { opacity: 0.85 },
                loading && { opacity: 0.7 },
              ]}
            >
              {loading ? (
                <ActivityIndicator color={colors.onBrandPrimary} />
              ) : (
                <Text style={styles.btnText}>Entrar</Text>
              )}
            </Pressable>

            <View style={styles.hintBox}>
              <Ionicons
                name="information-circle-outline"
                size={16}
                color={colors.onSurfaceSecondary}
              />
              <Text style={styles.hintText}>
                Demo: demo@estufa.com / demo1234
              </Text>
            </View>
          </View>
        </ScrollView>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  hero: { height: 320, width: "100%" },
  heroContent: {
    flex: 1,
    padding: spacing.xl,
    justifyContent: "flex-start",
  },
  logoPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: colors.brand,
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: radius.pill,
    alignSelf: "flex-start",
    marginTop: spacing.xxl,
  },
  logoText: {
    color: colors.onBrandPrimary,
    fontWeight: "600",
    fontSize: 13,
    letterSpacing: 0.3,
  },
  form: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: colors.onSurface,
    letterSpacing: -0.5,
  },
  subtitle: {
    marginTop: spacing.sm,
    fontSize: 15,
    color: colors.muted,
    lineHeight: 22,
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.onSurfaceSecondary,
    marginBottom: spacing.sm,
  },
  inputWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    height: 52,
    borderWidth: 1,
    borderColor: colors.border,
  },
  input: {
    flex: 1,
    fontSize: 15,
    color: colors.onSurface,
  },
  error: {
    marginTop: spacing.md,
    color: colors.error,
    fontSize: 13,
    fontWeight: "500",
  },
  btn: {
    marginTop: spacing.xl,
    backgroundColor: colors.brandPrimary,
    height: 54,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
  },
  btnText: {
    color: colors.onBrandPrimary,
    fontSize: 16,
    fontWeight: "600",
    letterSpacing: 0.2,
  },
  hintBox: {
    marginTop: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    padding: spacing.md,
    backgroundColor: colors.brandTertiary,
    borderRadius: radius.md,
  },
  hintText: {
    color: colors.onSurfaceSecondary,
    fontSize: 12.5,
  },
});
