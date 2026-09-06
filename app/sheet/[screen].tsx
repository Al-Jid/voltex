import { useLocalSearchParams } from 'expo-router';
import { LogSaleScreen } from '../../src/features/sales/SalesScreens';
import { SubmitCountScreen } from '../../src/features/stock/StockScreens';
import { NewRequestScreen } from '../../src/features/operations/RequestScreens';
import { CapturePhotoScreen } from '../../src/features/operations/PhotoScreens';
import { ForgotPasswordScreen } from '../../src/features/account/AccountScreens';
import { Empty, Screen, useUI } from '../../src/components/ui';
const screens = { 'log-sale': LogSaleScreen, 'submit-count': SubmitCountScreen, 'new-request': NewRequestScreen, 'capture-photo': CapturePhotoScreen, 'forgot-password': ForgotPasswordScreen };
export default function SheetRoute() {
  const { screen } = useLocalSearchParams<{ screen: string }>(); const { tx } = useUI(); const Component = screens[screen as keyof typeof screens];
  return Component ? <Component /> : <Screen back title={tx('Page not found', 'الصفحة غير موجودة')}><Empty title={tx('This form is unavailable', 'هذا النموذج غير متاح')} detail={tx('Go back to continue.', 'ارجع للمتابعة.')} /></Screen>;
}
