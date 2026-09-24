import { useEffect, useState } from "react";
import { Platform } from "react-native";
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { apiFetch } from "@/src/api/client";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export function useNotifications() {
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null);

  useEffect(() => {
    registerForPushNotificationsAsync().then(async (token) => {
      if (token) {
        setExpoPushToken(token);
        console.log("====================================");
        console.log("SEU EXPO PUSH TOKEN:", token);
        console.log("====================================");

        // --- ENVIA O TOKEN PARA O BACKEND SAVE NO BANCO ---
        try {
          await apiFetch("/auth/push-token", {
            method: "POST",
            body: JSON.stringify({ push_token: token }),
          });
          console.log("Push token registrado com sucesso no Azure SQL!");
        } catch (err) {
          console.error("Erro ao enviar Push Token para o backend:", err);
        }
      }
    });
  }, []);

  return { expoPushToken };
}

async function registerForPushNotificationsAsync() {
  if (!Device.isDevice) {
    console.log("Notificações Push funcionam apenas em dispositivos físicos.");
    return null;
  }

  const { granted: existingGranted } = await Notifications.getPermissionsAsync();
  let isGranted = existingGranted;

  if (!isGranted) {
    const { granted } = await Notifications.requestPermissionsAsync();
    isGranted = granted;
  }

  if (!isGranted) {
    console.log("Permissão para notificações foi negada!");
    return null;
  }

  if (Platform.OS === "android") {
    Notifications.setNotificationChannelAsync("default", {
      name: "default",
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#10B981",
    });
  }

  const tokenData = await Notifications.getExpoPushTokenAsync();
  return tokenData.data;
}