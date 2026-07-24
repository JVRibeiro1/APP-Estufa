import { Redirect } from "expo-router";
import { useAuth } from "@/src/context/auth";
import { View, ActivityIndicator } from "react-native";
import { colors } from "@/src/theme";

export default function Index() {
  const { user, loading } = useAuth();
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
  return user ? (
    <Redirect href="/(app)/dashboard" />
  ) : (
    <Redirect href="/(auth)/login" />
  );
}
