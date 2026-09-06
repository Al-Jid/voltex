import { useRef, useState } from 'react';
import { Alert, Image, Linking, View } from 'react-native';
import { router } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { Directory, File, Paths } from 'expo-file-system';
import { Button, Card, Empty, Field, Label, Pill, Screen, useUI } from '../../components/ui';
import { AppIcon } from '../../components/AppIcon';
import { makeId, useDemo, type ShelfPhoto } from '../../demo/DemoProvider';

function PhotoPreview({ uri }: { uri: string }) { const [failed, setFailed] = useState(false); const { tx } = useUI(); return failed ? <Empty title={tx('Photo unavailable', 'الصورة غير متاحة')} detail={tx('The local file could not be opened.', 'تعذّر فتح الملف المحلي.')} /> : <Image accessibilityLabel={tx('Shelf photo', 'صورة الرف')} source={{ uri }} onError={() => setFailed(true)} style={{ width: '100%', aspectRatio: 4 / 3, borderRadius: 12 }} />; }
export function ShelfScreen() {
  const { state } = useDemo(); const { tx, date } = useUI();
  return <Screen back title={tx('Shelf & photos', 'الأرفف والصور')} subtitle={tx('Citystars · Display quality', 'سيتي ستارز · جودة العرض')} action={{ icon: 'camera', label: tx('Capture photo', 'التقاط صورة'), run: () => router.push('/sheet/capture-photo') }}>
    <Card tinted><Label bold size={23}>{tx('A clear picture of your work.', 'صورة واضحة لشغلك.')}</Label><Label>{tx('Keep products visible, prices readable and the full shelf in frame.', 'خلّي المنتجات واضحة والأسعار مقروءة والرف كامل داخل الصورة.')}</Label></Card>
    {!state.photos.length && <Empty title={tx('Your first shelf story starts here', 'أول صورة لشغلك تبدأ هنا')} detail={tx('Take a photo or select one from your library. Nothing is uploaded.', 'التقط صورة أو اختر واحدة من المعرض. لن يتم رفع أي شيء.')} />}
    {state.photos.map(p => <Card key={p.id}><PhotoPreview uri={p.uri} /><Pill text={tx('Saved locally · not reviewed', 'محفوظ محليًا · لم يُراجع')} /><Label bold>{p.note || tx('Shelf display', 'عرض الرف')}</Label><Label muted size={12}>{date(p.date)} · {p.source === 'camera' ? tx('Camera', 'الكاميرا') : tx('Photo library', 'المعرض')}</Label><Label size={12}>{p.coords ? `${p.coords.latitude.toFixed(5)}, ${p.coords.longitude.toFixed(5)}` : tx('No location attached', 'بدون موقع مرفق')}</Label></Card>)}
    <Button title={tx('Add shelf photo', 'إضافة صورة للرف')} onPress={() => router.push('/sheet/capture-photo')} />
  </Screen>;
}
export function CapturePhotoScreen() {
  const { update } = useDemo(); const { tx, colors: c } = useUI(); const [image, setImage] = useState<{ uri: string; source: ShelfPhoto['source'] } | null>(null); const [note, setNote] = useState(''); const [coords, setCoords] = useState<ShelfPhoto['coords']>(); const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const saved = useRef(false);
  const busyRef = useRef(false);
  function permissionInfo() { Alert.alert(tx('Permission needed', 'مطلوب إذن الوصول'), tx('You can enable access in device settings, or continue without it.', 'يمكنك السماح بالوصول من إعدادات الجهاز أو المتابعة بدونه.'), [{ text: tx('Close', 'إغلاق'), style: 'cancel' }, { text: tx('Settings', 'الإعدادات'), onPress: () => { void Linking.openSettings().catch(() => setError(tx('Open device settings manually.', 'افتح إعدادات الجهاز يدويًا.'))); } }]); }
  async function pick(source: ShelfPhoto['source']) {
    if (busyRef.current) return; busyRef.current = true; setBusy(true); setError('');
    try {
      if (source === 'camera') { const permission = await ImagePicker.requestCameraPermissionsAsync(); if (!permission.granted) { permissionInfo(); return; } }
      const result = source === 'camera' ? await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.75 }) : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.75 });
      if (!result.canceled && result.assets[0]) { setImage({ uri: result.assets[0].uri, source }); setCoords(undefined); }
    } catch { setError(tx('Could not open the camera or library. Try again.', 'تعذّر فتح الكاميرا أو المعرض. حاول مجددًا.')); }
    finally { busyRef.current = false; setBusy(false); }
  }
  async function attachLocation() {
    if (busyRef.current) return; busyRef.current = true; setBusy(true); setError('');
    try {
      const permission = await Location.requestForegroundPermissionsAsync(); if (!permission.granted) { permissionInfo(); return; }
      if (!await Location.hasServicesEnabledAsync()) { setError(tx('Enable location services, then try again.', 'فعّل خدمات الموقع ثم حاول مجددًا.')); return; }
      const location = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }); setCoords({ latitude: location.coords.latitude, longitude: location.coords.longitude });
    } catch { setError(tx('Could not get your location. You can save without it.', 'تعذّر تحديد موقعك. يمكنك الحفظ بدونه.')); }
    finally { busyRef.current = false; setBusy(false); }
  }
  function save() {
    if (!image || saved.current || busyRef.current) return;
    saved.current = true;
    try {
      const id = makeId('P'); const dir = new Directory(Paths.document, 'voltex-shelf'); dir.create({ idempotent: true, intermediates: true });
      const extension = image.uri.split('.').pop()?.split('?')[0]; const safeExtension = extension && /^[a-zA-Z0-9]{2,5}$/.test(extension) ? extension : 'jpg';
      const destination = new File(dir, `${id}.${safeExtension}`); new File(image.uri).copy(destination);
      update(s => ({ ...s, photos: [{ id, uri: destination.uri, source: image.source, note: note.trim(), date: new Date().toISOString(), coords }, ...s.photos] })); router.replace('/detail/shelf');
    } catch { saved.current = false; setError(tx('Could not save the photo. Check device storage and retry.', 'تعذّر حفظ الصورة. راجع مساحة الجهاز وأعد المحاولة.')); }
  }
  return <Screen back title={tx('Capture photo', 'التقاط صورة')} subtitle={tx('Frame it. Review it. Save it.', 'صوّر. راجع. احفظ.')}>
    {image ? <PhotoPreview key={image.uri} uri={image.uri} /> : <View style={{ aspectRatio: 4 / 3, borderWidth: 1, borderStyle: 'dashed', borderColor: c.primary, backgroundColor: c.notice, borderRadius: 18, alignItems: 'center', justifyContent: 'center', gap: 16 }}><AppIcon name="camera" size={52} color={c.primary} /><Label>{tx('Full shelf · clear labels · good lighting', 'رف كامل · أسعار واضحة · إضاءة جيدة')}</Label></View>}
    <Button title={image ? tx('Retake photo', 'إعادة التصوير') : tx('Open camera', 'فتح الكاميرا')} disabled={busy} onPress={() => void pick('camera')} /><Button title={tx('Choose from library', 'اختيار من المعرض')} secondary disabled={busy} onPress={() => void pick('library')} />
    <Field label={tx('Photo notes', 'ملاحظات الصورة')} value={note} onChangeText={setNote} multiline maxLength={500} />
    <Card><Label bold>{tx('Location (optional)', 'الموقع (اختياري)')}</Label><Label muted>{coords ? `${coords.latitude.toFixed(5)}, ${coords.longitude.toFixed(5)}` : tx('Attach your current device location, not verified capture location.', 'أرفق موقع جهازك الحالي، وليس موقع تصوير متحققًا منه.')}</Label><Button title={coords ? tx('Remove location', 'إزالة الموقع') : tx('Attach current location', 'إرفاق الموقع الحالي')} secondary disabled={busy || !image} onPress={() => coords ? setCoords(undefined) : void attachLocation()} /></Card>
    {busy && <Label>{tx('Waiting for device…', 'في انتظار الجهاز…')}</Label>}{!!error && <Label>{error}</Label>}
    <Button title={tx('Save photo locally', 'حفظ الصورة محليًا')} disabled={!image || busy} onPress={save} />
  </Screen>;
}
