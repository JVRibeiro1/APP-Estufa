# AlfaceAI — Gerenciador de Estufa Inteligente

## Visão Geral
App mobile React Native (Expo SDK 54) para monitorar uma estufa hidropônica de alface, com detecção precoce de doenças em alface via visão computacional (API externa) e notificações in-app.

## Stack
- Frontend: Expo Router 6, React Native 0.81, expo-image, expo-linear-gradient, expo-haptics, AsyncStorage
- Backend: FastAPI + Motor (MongoDB), JWT (python-jose) + bcrypt (passlib)
- MongoDB (Motor async)

## Funcionalidades (MVP)
1. **Login customizado** (email/senha, JWT 7 dias, AsyncStorage)
2. **Dashboard** — hero card + grid de sensores (Temperatura, Umidade Ar, Umidade Solo, Luz, CO2) com status ideal/atenção/alto, e alertas recentes; auto-refresh 30s + pull-to-refresh
3. **Alertas** — lista filtrável (Todos / Não lidos), badges de severidade, marca lido ao abrir
4. **Detalhe de alerta** — foto (hero), % de precisão, descrição, recomendações, CTA "Marcar como Resolvido"
5. **Perfil** — dados do usuário, preferências, logout
6. **Webhook público** (`POST /api/alerts/webhook`) — para a API externa de visão computacional pushar detecções
7. **Sensor ingest público** (`POST /api/sensors/data`) — para o gateway físico pushar leituras

## Auth
Usuário demo semeado: `demo@estufa.com` / `demo1234`. JWT retornado em `/api/auth/login`, enviado como `Authorization: Bearer …`.

## Notas
- Push notifications reais NÃO configuradas (usuário optou por notificações in-app apenas). O badge no sino e o auto-refresh do dashboard cobrem a UX de "chegou um novo alerta" no Expo Go.
- Design: paleta verde botânica (`#0A4C36` / `#158348`), Terracotta `#C84C31` para erro, base iOS-native clean. Strings 100% PT-BR.
