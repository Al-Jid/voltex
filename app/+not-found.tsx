import { router } from 'expo-router';
import { Button, Empty, Screen, useUI } from '../src/components/ui';
export default function NotFoundScreen() {
  const { tx } = useUI();
  return <Screen back title={tx('Page not found', 'الصفحة غير موجودة')}><Empty title={tx('This link is unavailable', 'هذا الرابط غير متاح')} detail={tx('Return to the demo home to continue.', 'ارجع للرئيسية التجريبية للمتابعة.')} /><Button title={tx('Open home', 'فتح الرئيسية')} onPress={() => router.replace('/(tabs)/home')} /></Screen>;
}
