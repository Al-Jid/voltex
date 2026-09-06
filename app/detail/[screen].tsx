import { useLocalSearchParams } from 'expo-router';
import { SaleDetailScreen } from '../../src/features/sales/SalesScreens';
import { ChallengeScreen, LeaderboardScreen } from '../../src/features/rewards/RewardsScreens';
import { AttendanceScreen, AttendanceLogScreen } from '../../src/features/operations/AttendanceScreens';
import { RequestsScreen, RequestDetailScreen } from '../../src/features/operations/RequestScreens';
import { ShelfScreen } from '../../src/features/operations/PhotoScreens';
import { ProfileScreen, SettingsScreen, NotificationsScreen, HelpScreen } from '../../src/features/account/AccountScreens';
import { Empty, Screen, useUI } from '../../src/components/ui';
const screens = { sale: SaleDetailScreen, challenge: ChallengeScreen, leaderboard: LeaderboardScreen, attendance: AttendanceScreen, 'attendance-log': AttendanceLogScreen, requests: RequestsScreen, request: RequestDetailScreen, shelf: ShelfScreen, profile: ProfileScreen, settings: SettingsScreen, notifications: NotificationsScreen, help: HelpScreen };
export default function DetailRoute() {
  const { screen } = useLocalSearchParams<{ screen: string }>(); const { tx } = useUI();
  const Component = screens[screen as keyof typeof screens];
  return Component ? <Component /> : <Screen back title={tx('Page not found', 'الصفحة غير موجودة')}><Empty title={tx('This page is unavailable', 'هذه الصفحة غير متاحة')} detail={tx('Go back to continue.', 'ارجع للمتابعة.')} /></Screen>;
}
