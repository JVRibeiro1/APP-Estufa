import { Tabs } from "expo-router";
import { useAuth } from "@/src/context/auth";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/src/theme";
import { Platform } from "react-native";

export default function AppLayout() {
  const { user } = useAuth();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.brandPrimary,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: Platform.OS === "ios" ? 84 : 64,
          paddingTop: 6,
          paddingBottom: Platform.OS === "ios" ? 24 : 8,
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: "Estufa",
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? "leaf" : "leaf-outline"} size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="alerts"
        options={{
          title: "Alertas",
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? "notifications" : "notifications-outline"} size={22} color={color} />
          ),
        }}
      />

<Tabs.Screen
  name="admin"
  options={{
    title: "Admin",
    tabBarItemStyle: (user?.Adm || user?.adm) ? undefined : { display: "none" },
    tabBarIcon: ({ color, focused }) => (
      <Ionicons
        name={focused ? "shield-checkmark" : "shield-checkmark-outline"}
        size={22}
        color={color}
      />
    ),
  }}
/>

      <Tabs.Screen
        name="settings"
        options={{
          title: "Perfil",
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? "person-circle" : "person-circle-outline"} size={24} color={color} />
          ),
        }}
      />
      <Tabs.Screen name="alerts/[id]" options={{ href: null }} />
    </Tabs>
  );
}