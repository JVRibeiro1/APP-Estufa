import { Stack, useRouter, useSegments } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";
import { LogBox, View, ActivityIndicator } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { StatusBar } from "expo-status-bar";

import { useNotifications } from "@/src/hooks/useNotifications";
import { useIconFonts } from "@/src/hooks/use-icon-fonts";
import { AuthProvider, useAuth } from "@/src/context/auth";
import { colors } from "@/src/theme";

LogBox.ignoreAllLogs(true);

SplashScreen.preventAutoHideAsync();

function AuthGate() {
  const { user, loading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  // Inicializa o registro de notificações push
  useNotifications();

  useEffect(() => {
    if (loading) return;
    const inAuthGroup = segments[0] === "(auth)";
    const isRootPath = !segments[0];

    if (!user && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (user && (inAuthGroup || isRootPath)) {
      router.replace("/(app)/dashboard");
    }
  }, [user, loading, segments]);

  if (loading) {
    return (
      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: colors.surface,
        }}
      >
        <ActivityIndicator size="large" color={colors.brandPrimary} />
      </View>
    );
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}

export default function RootLayout() {
  const [loaded, error] = useIconFonts();

  useEffect(() => {
    if (loaded || error) {
      SplashScreen.hideAsync();
    }
  }, [loaded, error]);

  if (!loaded && !error) return null;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <AuthProvider>
          <StatusBar style="dark" />
          <AuthGate />
        </AuthProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}