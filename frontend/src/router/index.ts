import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('../layouts/MainLayout.vue'),
      children: [
        { path: '', name: 'Dashboard', component: () => import('../views/DashboardView.vue') },
        { path: 'carriers', name: 'Carriers', component: () => import('../views/references/CarriersView.vue') },
        { path: 'buyers', name: 'Buyers', component: () => import('../views/references/BuyersView.vue') },
        { path: 'materials', name: 'Materials', component: () => import('../views/references/MaterialsView.vue') },
        { path: 'vehicles', name: 'Vehicles', component: () => import('../views/references/VehiclesView.vue') },
        { path: 'machinery', name: 'Machinery', component: () => import('../views/references/MachineryView.vue') },
        { path: 'employees', name: 'Employees', component: () => import('../views/references/EmployeesView.vue') },
        { path: 'users', name: 'Users', component: () => import('../views/references/UsersView.vue'), meta: { role: 'admin' } },
        { path: 'trip-invoices', name: 'TripInvoices', component: () => import('../views/TripInvoicesView.vue') },
        { path: 'gsm-report', name: 'GSMReport', component: () => import('../views/GSMReportView.vue') },
        { path: 'machinery-sessions', name: 'MachinerySessions', component: () => import('../views/MachinerySessionsView.vue') },
        { path: 'payroll', name: 'Payroll', component: () => import('../views/PayrollView.vue') },
        { path: 'delivery-acts', name: 'DeliveryActs', component: () => import('../views/DeliveryActsView.vue') },
        { path: 'settings', name: 'Settings', component: () => import('../views/SettingsView.vue'), meta: { role: 'admin' } },
        { path: 'objects/:id', name: 'ObjectDetails', component: () => import('../views/ObjectDetailsView.vue') },
      ],
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) return next()
  if (!auth.isLoggedIn) return next('/login')
  if (!auth.user) await auth.fetchUser()
  if (to.meta.role && auth.user?.role !== to.meta.role) return next('/')
  next()
})

export default router
