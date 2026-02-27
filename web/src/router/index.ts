import { createRouter, createWebHistory } from 'vue-router'
import PortfolioView from '@/views/PortfolioView.vue'
import TemplatesView from '@/views/TemplatesView.vue'
import CompareView from '@/views/CompareView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'portfolio',
      component: PortfolioView
    },
    {
      path: '/templates',
      name: 'templates',
      component: TemplatesView
    },
    {
      path: '/compare',
      name: 'compare',
      component: CompareView
    }
  ]
})

export default router
