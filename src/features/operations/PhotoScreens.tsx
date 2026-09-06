import { useRef, useState } from 'react';
import { Alert, Image, Linking, Modal, Pressable, ScrollView, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { Directory, File, Paths } from 'expo-file-system';
import { Button, Card, Empty, Field, Label, Pill, Screen, useUI } from '../../components/ui';
import { AppIcon } from '../../components/AppIcon';
import { makeId, useDemo, type ShelfPhoto } from '../../demo/DemoProvider';
import { ReviewFeedback } from '../../management/PromoterManagement';
import { useManagement } from '../../management/ManagementProvider';

function PhotoPreview({ uri }: { uri: string }) { const [failed, setFailed] = useState(false); const { tx } = useUI(); return failed ? <Empty title={tx('Photo unavailable', 'الصورة غير متاحة')} detail={tx('The local file could not be opened.', 'تعذّر فتح الملف المحلي.')} /> : <Image accessibilityLabel={tx('Shelf photo', 'صورة الرف')} source={{ uri }} onError={() => setFailed(true)} style={{ width: '100%', aspectRatio: 4 / 3, borderRadius: 12 }} />; }
export function ShelfScreen() {
  const { state, update } = useDemo(); const { tx, date, colors: c } = useUI(); const management = useManagement();
  const [selectedId, setSelectedId] = useState<string | null>(null); const [editNote, setEditNote] = useState(''); const [message, setMessage] = useState('');
  const selected = state.photos.find(p => p.id === selectedId);
  function openPhoto(photo: ShelfPhoto) { setSelectedId(photo.id); setEditNote(photo.note); setMessage(''); }
  function removePhoto(photo: ShelfPhoto) {
    Alert.alert(tx('Remove this local photo?', 'حذف هذه الصورة المحلية؟'), tx('This removes your saved copy from this demo. The original in your library is unchanged.', 'سيُحذف الملف المحفوظ داخل النسخة التجريبية، وتبقى الصورة الأصلية في المعرض.'), [
      { text: tx('Keep photo', 'الاحتفاظ بالصورة'), style: 'cancel' },
      { text: tx('Remove', 'حذف'), style: 'destructive', onPress: () => {
        try {
          const folder = new Directory(Paths.document, 'voltex-shelf').uri.replace(/\/$/, '') + '/';
          if (photo.uri.startsWith(folder)) { const file = new File(photo.uri); if (file.exists) file.delete(); }
          update(s => ({ ...s, photos: s.photos.filter(p => p.id !== photo.id) })); setSelectedId(null);
        } catch { setMessage(tx('Could not remove the saved copy. Try again.', 'تعذّر حذف النسخة المحفوظة. حاول مجددًا.')); }
      } },
    ]);
  }
  return <Screen back title={tx('Shelf & photos', 'الأرفف والصور')} subtitle={tx('Citystars · Display quality', 'سيتي ستارز · جودة العرض')} action={{ icon: 'camera', label: tx('Capture photo', 'التقاط صورة'), run: () => router.push('/sheet/capture-photo') }}>
    <Card tinted><Label bold size={23}>{tx('A clear picture of your work.', 'صورة واضحة لشغلك.')}</Label><Label>{tx('Keep products visible, prices readable and the full shelf in frame.', 'خلّي المنتجات واضحة والأسعار مقروءة والرف كامل داخل الصورة.')}</Label></Card>
    {!state.photos.length && <Empty title={tx('Your first shelf story starts here', 'أول صورة لشغلك تبدأ هنا')} detail={tx('Take a photo or select one from your library. Nothing is uploaded.', 'التقط صورة أو اختر واحدة من المعرض. لن يتم رفع أي شيء.')} />}
    {state.photos.map(p => <Card key={p.id}><Pressable accessibilityRole="button" accessibilityLabel={tx('Open photo details', 'فتح تفاصيل الصورة')} onPress={() => openPhoto(p)}><PhotoPreview uri={p.uri} /></Pressable><Pill text={tx('Saved locally', 'محفوظ محليًا')} /><ReviewFeedback id={p.id} kind="photo" /><Label bold>{p.note || tx('Shelf display', 'عرض الرف')}</Label><Label muted size={12}>{date(p.date)} · {p.source === 'camera' ? tx('Camera', 'الكاميرا') : tx('Photo library', 'المعرض')}</Label><Label size={12}>{p.coords ? `${p.coords.latitude.toFixed(5)}, ${p.coords.longitude.toFixed(5)}` : tx('No location attached', 'بدون موقع مرفق')}</Label><Button title={tx('View photo details', 'عرض تفاصيل الصورة')} secondary onPress={() => openPhoto(p)} /></Card>)}
    <Button title={tx('Add shelf photo', 'إضافة صورة للرف')} onPress={() => router.push('/sheet/capture-photo')} />
    <Modal visible={!!selected} animationType="slide" onRequestClose={() => setSelectedId(null)}>
      <SafeAreaView style={{ flex: 1, backgroundColor: c.background }}><ScrollView contentContainerStyle={{ padding: 20, gap: 16, width: '100%', maxWidth: 680, alignSelf: 'center' }}>
        <Label bold size={24}>{tx('Photo details', 'تفاصيل الصورة')}</Label>
        {selected && <><PhotoPreview key={selected.id} uri={selected.uri} /><Pill text={tx('Local photo · not uploaded', 'صورة محلية · لم تُرفع')} /><Label>{date(selected.date)}</Label><Label muted>{selected.source === 'camera' ? tx('Source: camera', 'المصدر: الكاميرا') : tx('Source: photo library', 'المصدر: المعرض')}</Label><Label muted>{selected.coords ? `${selected.coords.latitude.toFixed(5)}, ${selected.coords.longitude.toFixed(5)}` : tx('No location attached', 'بدون موقع مرفق')}</Label><Field label={tx('Edit notes', 'تعديل الملاحظات')} value={editNote} onChangeText={setEditNote} multiline maxLength={500} /><Button title={tx('Save notes', 'حفظ الملاحظات')} onPress={() => { if (selected.note !== editNote.trim()) { update(s => ({ ...s, photos: s.photos.map(p => p.id === selected.id ? { ...p, note: editNote.trim() } : p) })); management.change(`Photo ${selected.id}: notes updated, review reopened`, s => ({ ...s, reviews: s.reviews.filter(r => !(r.id === selected.id && r.kind === 'photo')) })); } setMessage(tx('Notes saved locally. Changed notes reopen supervisor review.', 'تم حفظ الملاحظات محليًا. تغييرها يعيد فتح مراجعة المشرف.')); }} /><Button title={tx('Remove local photo', 'حذف الصورة المحلية')} secondary onPress={() => removePhoto(selected)} /></>}
        {!!message && <Label>{message}</Label>}<Button title={tx('Close', 'إغلاق')} secondary onPress={() => setSelectedId(null)} />
      </ScrollView></SafeAreaView>
    </Modal>
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
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      const permission = await Location.requestForegroundPermissionsAsync(); if (!permission.granted) { permissionInfo(); return; }
      if (!await Location.hasServicesEnabledAsync()) { setError(tx('Enable location services, then try again.', 'فعّل خدمات الموقع ثم حاول مجددًا.')); return; }
      const location = await Promise.race([Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }), new Promise<never>((_, reject) => { timer = setTimeout(() => reject(new Error('Location timeout')), 15000); })]); setCoords({ latitude: location.coords.latitude, longitude: location.coords.longitude });
    } catch { setError(tx('Could not get your location. You can save without it.', 'تعذّر تحديد موقعك. يمكنك الحفظ بدونه.')); }
    finally { if (timer) clearTimeout(timer); busyRef.current = false; setBusy(false); }
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
