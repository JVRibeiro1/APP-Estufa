import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Switch,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { apiFetch } from "@/src/api/client";
import { colors, spacing, radius } from "@/src/theme";

export default function AdminScreen() {
  // Estados para Criar Usuário
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [loadingUser, setLoadingUser] = useState(false);

  // Estados para Criar Estufa
  const [nomeEstufa, setNomeEstufa] = useState("");
  const [loadingEstufa, setLoadingEstufa] = useState(false);

  // Estados para Vincular Usuário à Estufa
  const [usuarioIdVinculo, setUsuarioIdVinculo] = useState("");
  const [estufaIdVinculo, setEstufaIdVinculo] = useState("");
  const [loadingVinculo, setLoadingVinculo] = useState(false);

  const handleCreateUser = async () => {
    if (!email || !senha || !nome) {
      Alert.alert("Atenção", "Preencha todos os campos do usuário.");
      return;
    }
    setLoadingUser(true);
    try {
      await apiFetch("/admin/users", {
        method: "POST",
        body: JSON.stringify({ nome, email, senha, is_admin: isAdmin }),
      });
      Alert.alert("Sucesso", "Novo usuário cadastrado com sucesso!");
      setNome("");
      setEmail("");
      setSenha("");
      setIsAdmin(false);
    } catch (e: any) {
      Alert.alert("Erro", e.message || "Erro ao criar usuário");
    } finally {
      setLoadingUser(false);
    }
  };

  const handleCreateEstufa = async () => {
    if (!nomeEstufa) {
      Alert.alert("Atenção", "Informe o nome da estufa.");
      return;
    }
    setLoadingEstufa(true);
    try {
      await apiFetch("/admin/estufas", {
        method: "POST",
        body: JSON.stringify({ nome_estufa: nomeEstufa }),
      });
      Alert.alert("Sucesso", "Nova estufa cadastrada com sucesso!");
      setNomeEstufa("");
    } catch (e: any) {
      Alert.alert("Erro", e.message || "Erro ao criar estufa");
    } finally {
      setLoadingEstufa(false);
    }
  };

  const handleVincular = async () => {
    if (!usuarioIdVinculo || !estufaIdVinculo) {
      Alert.alert("Atenção", "Informe o ID do usuário e o ID da estufa.");
      return;
    }
    setLoadingVinculo(true);
    try {
      await apiFetch("/admin/vincular-estufa", {
        method: "POST",
        body: JSON.stringify({
          usuario_id: Number(usuarioIdVinculo),
          estufa_id: Number(estufaIdVinculo),
        }),
      });
      Alert.alert("Sucesso", "Usuário vinculado à estufa com sucesso!");
      setUsuarioIdVinculo("");
      setEstufaIdVinculo("");
    } catch (e: any) {
      Alert.alert("Erro", e.message || "Erro ao vincular estufa");
    } finally {
      setLoadingVinculo(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>Painel do Administrador</Text>

        {/* 1. SEÇÃO CADASTRAR USUÁRIO */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Cadastrar Novo Usuário</Text>
          <TextInput
            style={styles.input}
            placeholder="Nome Completo"
            placeholderTextColor="#888"
            value={nome}
            onChangeText={setNome}
          />
          <TextInput
            style={styles.input}
            placeholder="E-mail"
            placeholderTextColor="#888"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />
          <TextInput
            style={styles.input}
            placeholder="Senha"
            placeholderTextColor="#888"
            value={senha}
            onChangeText={setSenha}
            secureTextEntry
          />
          <View style={styles.switchRow}>
            <Text style={styles.label}>Tornar Administrador?</Text>
            <Switch value={isAdmin} onValueChange={setIsAdmin} />
          </View>
          <TouchableOpacity
            style={styles.button}
            onPress={handleCreateUser}
            disabled={loadingUser}
          >
            <Text style={styles.buttonText}>
              {loadingUser ? "Salvando..." : "Cadastrar Usuário"}
            </Text>
          </TouchableOpacity>
        </View>

        {/* 3. SEÇÃO VINCULAR USUÁRIO A ESTUFA (N:N) */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Vincular Usuário à Estufa</Text>
          <TextInput
            style={styles.input}
            placeholder="ID do Usuário (ex: 2)"
            placeholderTextColor="#888"
            value={usuarioIdVinculo}
            onChangeText={setUsuarioIdVinculo}
            keyboardType="numeric"
          />
          <TextInput
            style={styles.input}
            placeholder="ID da Estufa (ex: 1)"
            placeholderTextColor="#888"
            value={estufaIdVinculo}
            onChangeText={setEstufaIdVinculo}
            keyboardType="numeric"
          />
          <TouchableOpacity
            style={[styles.button, { backgroundColor: "#3B82F6" }]}
            onPress={handleVincular}
            disabled={loadingVinculo}
          >
            <Text style={styles.buttonText}>
              {loadingVinculo ? "Vinculando..." : "Vincular Acesso"}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.surface },
  scroll: { padding: spacing.lg, gap: spacing.xl },
  title: { fontSize: 24, fontWeight: "700", color: colors.onSurface },
  card: {
    backgroundColor: colors.surfaceSecondary,
    padding: spacing.lg,
    borderRadius: radius.md,
    gap: spacing.md,
  },
  cardTitle: { fontSize: 18, fontWeight: "600", color: colors.onSurface },
  input: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: 12,
    borderRadius: radius.sm,
    fontSize: 15,
    color: colors.onSurface,
  },
  switchRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  label: { fontSize: 14, color: colors.onSurface },
  button: {
    backgroundColor: colors.brandPrimary,
    paddingVertical: 14,
    borderRadius: radius.sm,
    alignItems: "center",
  },
  buttonText: { color: "#FFF", fontWeight: "700", fontSize: 15 },
});