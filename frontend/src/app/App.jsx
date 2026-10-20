import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import ProtectedRoute from '../components/common/ProtectedRoute'
import DashboardPage from '../features/dashboard/DashboardPage'
import MarketplacePage from '../features/marketplace/MarketplacePage'
import MyListingsPage from '../features/products/MyListingsPage'
import OrdersPage from '../features/orders/OrdersPage'
import ScanPage from '../features/scan/ScanPage'
import ProfilePage from '../features/profile/ProfilePage'
import AuthPage from '../pages/AuthPage'

function Protected({children,roles}) { return <ProtectedRoute roles={roles}>{children}</ProtectedRoute> }
export default function App(){
 return <Routes>
  <Route path="/login" element={<AuthPage mode="login"/>}/><Route path="/register" element={<AuthPage mode="register"/>}/>
  <Route element={<Protected><AppShell/></Protected>}>
   <Route path="/dashboard" element={<DashboardPage/>}/>
   <Route path="/scan" element={<Protected roles={['farmer','user']}><ScanPage/></Protected>}/>
   <Route path="/marketplace/produce" element={<MarketplacePage listingType="produce"/>}/>
   <Route path="/marketplace/supplies" element={<MarketplacePage listingType="supply"/>}/>
   <Route path="/my-listings" element={<Protected roles={['farmer','vendor']}><MyListingsPage/></Protected>}/>
   <Route path="/orders" element={<OrdersPage/>}/>
   <Route path="/sales" element={<OrdersPage/>}/>
   <Route path="/profile" element={<ProfilePage/>}/>
  </Route>
  <Route path="/" element={<Navigate to="/dashboard" replace/>}/><Route path="*" element={<Navigate to="/dashboard" replace/>}/>
 </Routes>
}
