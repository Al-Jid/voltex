import { useRef, useState } from 'react';
import { Alert, Keyboard, KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Icon, type IconName } from '../../components/Icon';
import { VoltexLogo } from '../../components/VoltexLogo';
import { usePreferences, type ThemeMode } from '../../theme/Preferences';
import { copy } from './copy';
import { router } from 'expo-router';

export default function LoginScreen() {
  const { colors: c, language, setLanguage, mode, setMode, isDark } = usePreferences();
  const t = copy[language];
  const rtl = language === 'ar';
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [visible, setVisible] = useState(false);
  const [remember, setRemember] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [focused, setFocused] = useState<'username' | 'password' | null>(null);
  const [panel, setPanel] = useState<'language' | 'appearance' | null>(null);
  const passwordRef = useRef<TextInput>(null);
  const usernameRef = useRef<TextInput>(null);
  const row = { flexDirection: rtl ? 'row-reverse' as const : 'row' as const };
  const textDirection = { textAlign: rtl ? 'right' as const : 'left' as const, writingDirection: rtl ? 'rtl' as const : 'ltr' as const };
  const usernameError = submitted && !username.trim();
  const passwordError = submitted && !password;

  function submit() {
    setSubmitted(true);
    if (!username.trim()) { usernameRef.current?.focus(); return; }
    if (!password) { passwordRef.current?.focus(); return; }
    Keyboard.dismiss();
    // No authentication simulation: connect an auth service before allowing navigation.
    Alert.alert(t.unavailable, t.unavailableBody);
  }
  const showBiometricInfo = () => Alert.alert(t.biometricTitle, t.biometricBody);
  const modes: { value: ThemeMode; icon: IconName }[] = [
    { value: 'light', icon: 'sun' }, { value: 'dark', icon: 'moon' }, { value: 'system', icon: 'system' },
  ];

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: c.background }]}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" showsVerticalScrollIndicator={false}>
          <View style={styles.page}>
            <View style={[styles.toolbar, row]}>
              <Pressable accessibilityRole="button" accessibilityLabel={t.appearance} onPress={() => setPanel('appearance')} style={({ pressed }) => [styles.themeButton, { opacity: pressed ? 0.5 : 1 }]}>
                <Icon name={isDark ? 'moon' : 'sun'} size={18} color={c.muted} />
              </Pressable>
              <Pressable accessibilityRole="button" accessibilityLabel={t.language} onPress={() => setPanel('language')} style={({ pressed }) => [styles.languageButton, { backgroundColor: c.surface, opacity: pressed ? 0.65 : 1 }]}>
                <Icon name="globe" size={15} color={c.primary} />
                <Text style={[styles.languageText, { color: c.primary }]}>{language === 'en' ? 'EN' : 'عربي'}</Text>
                <Icon name="chevron" size={14} color={c.primary} />
              </Pressable>
            </View>

            <View style={styles.brand}>
              <VoltexLogo dark={isDark} />
              <Text accessibilityRole="header" style={[styles.title, { color: c.text }]}>{t.welcome}</Text>
              <Text style={[styles.subtitle, { color: c.text }]}>{t.subtitle}</Text>
            </View>

            <View style={styles.form}>
              <Text nativeID="username-label" style={[styles.label, textDirection, { color: c.text }]}>{t.username}</Text>
              <View style={[styles.field, { backgroundColor: c.field, borderColor: usernameError ? c.error : focused === 'username' ? c.primary : c.border }]}>
                <TextInput ref={usernameRef} value={username} onChangeText={setUsername} accessibilityLabel={t.username} accessibilityLabelledBy="username-label"
                  placeholder="hassann.gamal" placeholderTextColor={c.muted} autoCapitalize="none" autoCorrect={false} autoComplete="username" textContentType="username"
                  returnKeyType="next" onSubmitEditing={() => passwordRef.current?.focus()} onFocus={() => setFocused('username')} onBlur={() => setFocused(null)}
                  style={[styles.input, { color: c.text, textAlign: 'left', writingDirection: 'ltr' }]} />
              </View>
              {usernameError && <Text accessibilityLiveRegion="polite" style={[styles.error, textDirection, { color: c.error }]}>{t.requiredUsername}</Text>}

              <Text nativeID="password-label" style={[styles.label, styles.passwordLabel, textDirection, { color: c.text }]}>{t.password}</Text>
              <View style={[styles.field, row, { backgroundColor: c.field, borderColor: passwordError ? c.error : focused === 'password' ? c.primary : c.border }]}>
                <TextInput ref={passwordRef} value={password} onChangeText={setPassword} accessibilityLabel={t.password} accessibilityLabelledBy="password-label"
                  placeholder="**********" placeholderTextColor={c.muted} secureTextEntry={!visible} autoCapitalize="none" autoCorrect={false}
                  autoComplete="current-password" textContentType="password" returnKeyType="go" onSubmitEditing={submit}
                  onFocus={() => setFocused('password')} onBlur={() => setFocused(null)}
                  style={[styles.input, { color: c.text, textAlign: 'left', writingDirection: 'ltr' }]} />
                <Pressable accessibilityRole="button" accessibilityLabel={visible ? t.hide : t.show} accessibilityState={{ checked: visible }}
                  onPress={() => setVisible(value => !value)} style={({ pressed }) => [styles.eyeButton, { opacity: pressed ? 0.5 : 1 }]}>
                  <Icon name={visible ? 'eyeOff' : 'eye'} size={19} color={c.muted} />
                </Pressable>
              </View>
              {passwordError && <Text accessibilityLiveRegion="polite" style={[styles.error, textDirection, { color: c.error }]}>{t.requiredPassword}</Text>}

              <View style={[styles.options, row]}>
                <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: remember }} accessibilityLabel={t.remember}
                  onPress={() => setRemember(value => !value)} style={[styles.remember, row]}>
                  <View style={[styles.checkbox, { backgroundColor: remember ? c.primary : 'transparent', borderColor: remember ? c.primary : c.border }]}>
                    {remember && <Icon name="check" size={14} color={c.onPrimary} />}
                  </View>
                  <Text style={[styles.rememberText, { color: c.text }]}>{t.remember}</Text>
                </Pressable>
                <Pressable accessibilityRole="button" onPress={() => router.push('/sheet/forgot-password')} style={({ pressed }) => [styles.forgot, { opacity: pressed ? 0.5 : 1 }]}>
                  <Text style={[styles.forgotText, { color: c.text }]}>{t.forgot}</Text>
                </Pressable>
              </View>

              <Pressable accessibilityRole="button" onPress={submit} style={({ pressed }) => [styles.login, { backgroundColor: c.primary, opacity: pressed ? 0.85 : 1 }]}>
                <Text style={[styles.loginText, { color: c.onPrimary }]}>{t.login}</Text>
              </Pressable>
              <Pressable accessibilityRole="button" onPress={() => router.replace('/(tabs)/home')} style={{ minHeight: 44, alignItems: 'center', justifyContent: 'center' }}>
                <Text style={{ color: c.primary, fontSize: 12 }}>{rtl ? 'استكشاف النسخة التجريبية بدون حساب' : 'Explore demo without an account'}</Text>
              </Pressable>
            </View>

            <View style={styles.biometrics}>
              <Text style={[styles.biometricCaption, { color: c.text }]}>{t.biometrics}</Text>
              <View style={styles.biometricRow}>
                <View style={[styles.rule, { backgroundColor: c.muted }]} />
                <View style={[styles.biometricButtons, row]}>
                  <Pressable accessibilityRole="button" accessibilityLabel={t.face} onPress={showBiometricInfo} style={({ pressed }) => [styles.biometricButton, { opacity: pressed ? 0.5 : 1 }]}>
                    <View style={[styles.biometricCircle, { backgroundColor: c.circle }]}><Icon name="face" size={29} color={c.muted} /></View>
                    <Text style={[styles.biometricLabel, { color: c.text }]}>{t.face}</Text>
                  </Pressable>
                  <Pressable accessibilityRole="button" accessibilityLabel={t.fingerprint} onPress={showBiometricInfo} style={({ pressed }) => [styles.biometricButton, { opacity: pressed ? 0.5 : 1 }]}>
                    <View style={[styles.biometricCircle, { backgroundColor: c.circle }]}><Icon name="fingerprint" size={30} color={c.muted} /></View>
                    <Text style={[styles.biometricLabel, { color: c.text }]}>{t.fingerprint}</Text>
                  </Pressable>
                </View>
                <View style={[styles.rule, { backgroundColor: c.muted }]} />
              </View>
            </View>

            <View style={styles.footer}>
              <View style={[styles.notice, { backgroundColor: c.notice, borderColor: c.border }]}>
                <Text style={[styles.noticeText, textDirection, { color: c.text }]}>{t.help}</Text>
              </View>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      <Modal visible={panel !== null} transparent animationType="fade" onRequestClose={() => setPanel(null)} statusBarTranslucent>
        <View style={styles.modalRoot}>
          <Pressable style={styles.scrim} accessibilityRole="button" accessibilityLabel={t.close} onPress={() => setPanel(null)} />
          <View accessibilityViewIsModal style={[styles.dialog, { backgroundColor: c.surface }]}>
            <View style={[styles.dialogHeader, row]}>
              <Text accessibilityRole="header" style={[styles.dialogTitle, { color: c.text }]}>{panel === 'language' ? t.language : t.appearance}</Text>
              <Pressable accessibilityRole="button" accessibilityLabel={t.close} onPress={() => setPanel(null)} style={styles.eyeButton}><Icon name="close" color={c.muted} /></Pressable>
            </View>
            {panel === 'language' ? (['en', 'ar'] as const).map(value => (
              <Pressable key={value} accessibilityRole="radio" accessibilityState={{ checked: language === value }} onPress={() => { setLanguage(value); setPanel(null); }}
                style={[styles.choice, row, { backgroundColor: language === value ? c.notice : c.surface }]}>
                <Text style={[styles.choiceText, { color: c.text }]}>{value === 'en' ? 'English' : 'العربية'}</Text>
                {language === value && <Icon name="check" color={c.primary} />}
              </Pressable>
            )) : modes.map(({ value, icon }) => (
              <Pressable key={value} accessibilityRole="radio" accessibilityState={{ checked: mode === value }} onPress={() => { setMode(value); setPanel(null); }}
                style={[styles.choice, row, { backgroundColor: mode === value ? c.notice : c.surface }]}>
                <Icon name={icon} color={c.primary} /><Text style={[styles.choiceText, styles.flex, textDirection, { color: c.text }]}>{t[value]}</Text>
                {mode === value && <Icon name="check" color={c.primary} />}
              </Pressable>
            ))}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 }, flex: { flex: 1 }, scroll: { flexGrow: 1 },
  page: { flexGrow: 1, width: '100%', maxWidth: 440, alignSelf: 'center', paddingHorizontal: 18, paddingBottom: 24 },
  toolbar: { alignItems: 'center', justifyContent: 'space-between', paddingTop: 10, minHeight: 48 },
  themeButton: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center', marginLeft: -10 },
  languageButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, minHeight: 44, paddingHorizontal: 9, borderRadius: 24 },
  languageText: { fontSize: 12 }, brand: { alignItems: 'center', marginTop: 64 },
  title: { fontSize: 25, fontWeight: '700', marginTop: 20, textAlign: 'center', letterSpacing: -0.5 },
  subtitle: { fontSize: 15, marginTop: 2, textAlign: 'center', lineHeight: 21 },
  form: { marginTop: 22 }, label: { fontSize: 11, letterSpacing: 0.5, marginBottom: 5 },
  field: { borderWidth: 0.8, borderRadius: 7, minHeight: 49, flexDirection: 'row', alignItems: 'center' },
  input: { flex: 1, minWidth: 0, minHeight: 47, paddingHorizontal: 13, paddingVertical: 12, fontSize: 14, letterSpacing: 0.5 },
  passwordLabel: { marginTop: 10 }, eyeButton: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  error: { fontSize: 12, lineHeight: 18, marginTop: 4 },
  options: { alignItems: 'center', justifyContent: 'space-between', gap: 8, minHeight: 34, marginTop: -4 },
  remember: { alignItems: 'center', gap: 6, minHeight: 44 },
  checkbox: { width: 17, height: 17, borderWidth: 1, borderRadius: 4, alignItems: 'center', justifyContent: 'center' },
  rememberText: { fontSize: 12 }, forgot: { minHeight: 44, justifyContent: 'center' }, forgotText: { fontSize: 10.5, letterSpacing: 0.25 },
  login: { minHeight: 49, alignItems: 'center', justifyContent: 'center', borderRadius: 7, marginTop: 6, padding: 12 },
  loginText: { fontSize: 14, fontWeight: '500', letterSpacing: 0.3 },
  biometrics: { marginTop: 25 }, biometricCaption: { textAlign: 'center', fontSize: 10.5, letterSpacing: 0.35 },
  biometricRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', marginTop: 15, gap: 12 },
  rule: { height: 0.8, width: '16%', marginTop: 19 }, biometricButtons: { justifyContent: 'center', gap: 12, flex: 1 },
  biometricButton: { alignItems: 'center', minWidth: 62 }, biometricCircle: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  biometricLabel: { fontSize: 10.5, letterSpacing: 0.35, marginTop: 6, textAlign: 'center' },
  footer: { flexGrow: 1, justifyContent: 'flex-end', paddingTop: 96 }, notice: { borderWidth: 0.8, borderRadius: 8, paddingHorizontal: 9, paddingVertical: 9 },
  noticeText: { fontSize: 11, lineHeight: 15 },
  modalRoot: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 }, scrim: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(12,8,24,0.45)' },
  dialog: { width: '100%', maxWidth: 360, padding: 18, borderRadius: 20 }, dialogHeader: { alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  dialogTitle: { fontSize: 20, fontWeight: '600' }, choice: { minHeight: 52, paddingHorizontal: 14, paddingVertical: 12, borderRadius: 12, marginBottom: 6, alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  choiceText: { fontSize: 16 },
});
