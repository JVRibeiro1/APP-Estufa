import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  Alert,
  StyleSheet,
  ScrollView,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Estufa, fetchMyGreenhouses, createTeamUser } from "@/src/api/client";
import { colors, spacing, radius } from "@/src/theme";

export default function AdminScreen() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [isAdm, setIsAdm] = useState(false);

  // Lista de estufas do Adm logado
  const [myEstufas, setMyEstufas] = useState<Estufa[]>([]);
  // IDs das estufas selecionadas para o novo usuário
  const [selectedEstufaIds, setSelectedEstufaIds] = useState<number[]>([]);

  useEffect(() => {
    async function loadEstufas() {
      try {
        const estufas = await fetchMyGreenhouses();
        setMyEstufas(estufas);
        // Por padrão, seleciona a primeira estufa da lista
        if (estufas.length > 0) {
          setSelectedEstufaIds([estufas[0].Id]);
        }
      } catch (err) {
        console.error("Erro ao carregar estufas:", err);
      }
    }
    loadEstufas();
  }, []);

  // Alterna a seleção da estufa (permite seleção múltipla)
  const toggleEstufaSelection = (id: number) => {
    if (selectedEstufaIds.includes(id)) {
      if (selectedEstufaIds.length === 1) {
        Alert.alert("Atenção", "O usuário precisa ter acesso a pelo menos uma estufa.");
        return;
      }
      setSelectedEstufaIds(selectedEstufaIds.filter((item) => item !== id));
    } else {
      setSelectedEstufaIds([...selectedEstufaIds, id]);
    }
  };

  const handleCreateUser = async () => {
    if (!nome || !email || !senha) {
      Alert.alert("Campos obrigatórios", "Preencha todos os campos.");
      return;
    }

    try {
      await createTeamUser({
        nome,
        email,
        senha,
        estufa_ids: selectedEstufaIds,
        adm: isAdm,
      });

      Alert.alert("Sucesso!", "Novo funcionário cadastrado com sucesso.");
      setNome("");
      setEmail("");
      setSenha("");
    } catch (error: any) {
      Alert.alert("Erro ao cadastrar", error.message);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Cadastrar Funcionário</Text>

      <Text style={styles.label}>Nome</Text>
      <TextInput style={styles.input} value={nome} onChangeText={setNome} placeholder="Ex: Maria Silva" />

      <Text style={styles.label}>E-mail</Text>
      <TextInput
        style={styles.input}
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
        placeholder="maria@empresa.com"
      />

      <Text style={styles.label}>Senha Temporária</Text>
      <TextInput
        style={styles.input}
        value={senha}
        onChangeText={setSenha}
        secureTextEntry
        placeholder="••••••••"
      />

      {/* Seleção de Estufas */}
      <Text style={styles.label}>Vincular às Estufas:</Text>
      <View style={styles.chipsRow}>
        {myEstufas.map((estufa) => {
          const selected = selectedEstufaIds.includes(estufa.Id);
          return (
            <Pressable
              key={estufa.Id}
              style={[styles.chip, selected && styles.chipSelected]}
              onPress={() => toggleEstufaSelection(estufa.Id)}
            >
              <Ionicons
                name={selected ? "checkbox" : "square-outline"}
                size={18}
                color={selected ? "#fff" : colors.muted}
              />
              <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
                {estufa.NomeEstufa}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <Pressable style={styles.btnSubmit} onPress={handleCreateUser}>
        <Text style={styles.btnText}>Cadastrar e Vincular</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: spacing.xl, backgroundColor: colors.surface },
  title: { fontSize: 20, fontWeight: "700", marginBottom: spacing.lg, color: colors.onSurface },
  label: { fontSize: 13, color: colors.muted, marginTop: spacing.md, marginBottom: 4 },
  input: {
    backgroundColor: colors.surfaceSecondary,
    padding: spacing.md,
    borderRadius: radius.md,
    color: colors.onSurface,
  },
  chipsRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, marginTop: spacing.xs },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceSecondary,
  },
  chipSelected: { backgroundColor: colors.brandPrimary },
  chipText: { fontSize: 13, color: colors.onSurface },
  chipTextSelected: { color: "#fff", fontWeight: "700" },
  btnSubmit: {
    backgroundColor: colors.brandPrimary,
    padding: spacing.md,
    borderRadius: radius.md,
    alignItems: "center",
    marginTop: spacing.xxl,
  },
  btnText: { color: "#fff", fontWeight: "700", fontSize: 15 },
});