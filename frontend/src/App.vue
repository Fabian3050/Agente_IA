<template>
  <!-- If not logged in, show LoginPage -->
  <LoginView
    v-if="!isLoggedIn"
    @login-success="handleLoginSuccess"
  />

  <!-- Main Application Layout -->
  <div v-else class="flex h-screen w-screen overflow-hidden bg-[#F7F9FB] font-sans antialiased text-[#1a2332]">
    <!-- Collapsible USACH Sidebar -->
    <Sidebar
      :current="currentPage"
      :collapsed="sidebarCollapsed"
      @nav="navigate"
      @toggle="sidebarCollapsed = !sidebarCollapsed"
    />

    <!-- Main Workspace Area -->
    <div class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
      <!-- Top Application Header -->
      <Header
        :page="currentPage"
        :user="currentUser"
        @nav="navigate"
        @logout="handleLogout"
      />

      <!-- Active View Content Container -->
      <main class="flex-1 p-6 overflow-hidden min-h-0 bg-[#F7F9FB]">
        <DashboardView
          v-if="currentPage === 'dashboard'"
          @nav="navigate"
        />

        <MonitoreoView
          v-else-if="currentPage === 'monitoreo'"
        />

        <ValidacionView
          v-else-if="currentPage === 'validacion'"
        />

        <AprobacionView
          v-else-if="currentPage === 'aprobacion'"
        />

        <AuditoriaView
          v-else-if="currentPage === 'auditoria'"
        />

        <ReportesView
          v-else-if="currentPage === 'reportes' || currentPage === 'recuperacion'"
        />

        <UsuariosView
          v-else-if="currentPage === 'usuarios'"
        />

        <ConfiguracionView
          v-else-if="currentPage === 'configuracion'"
        />

        <PerfilView
          v-else-if="currentPage === 'perfil'"
          :user="currentUser"
        />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Sidebar from './components/layout/Sidebar.vue'
import Header from './components/layout/Header.vue'
import LoginView from './views/LoginView.vue'
import DashboardView from './views/DashboardView.vue'
import MonitoreoView from './views/MonitoreoView.vue'
import ValidacionView from './views/ValidacionView.vue'
import AprobacionView from './views/AprobacionView.vue'
import AuditoriaView from './views/AuditoriaView.vue'
import ReportesView from './views/ReportesView.vue'
import UsuariosView from './views/UsuariosView.vue'
import ConfiguracionView from './views/ConfiguracionView.vue'
import PerfilView from './views/PerfilView.vue'

import { authService } from './services/authService'
import type { Page, User } from './types'

const isLoggedIn = ref(false)
const currentUser = ref<User | null>(null)
const currentPage = ref<Page>('dashboard')
const sidebarCollapsed = ref(false)

const navigate = (page: Page) => {
  currentPage.value = page
}

const handleLoginSuccess = (user: User) => {
  currentUser.value = user
  isLoggedIn.value = true
  currentPage.value = 'dashboard'
}

const handleLogout = () => {
  authService.logout()
  currentUser.value = null
  isLoggedIn.value = false
}

onMounted(async () => {
  // Check if session token exists
  if (authService.isAuthenticated()) {
    const user = authService.getStoredUser()
    if (user) {
      currentUser.value = user
      isLoggedIn.value = true
      // Validar validez del token con MS3 (/auth/me)
      try {
        const remoteUser = await authService.getCurrentUser()
        if (remoteUser) {
          currentUser.value = remoteUser
        }
      } catch {
        // Si el token expiró o es inválido, cerrar sesión
        handleLogout()
      }
    }
  }
})
</script>

