import { createRouter, createWebHistory } from 'vue-router'
import EventTimeline from './components/EventTimeline.vue'
import About from './components/About.vue'

const routes = [
  {
    path: '/',
    component: EventTimeline
  },
  {
    path: '/about',
    component: About
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 