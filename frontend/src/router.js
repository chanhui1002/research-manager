import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/papers' },
  { path: '/papers', component: () => import('./views/Papers.vue') },
  { path: '/books', component: () => import('./views/Books.vue') },
  { path: '/projects', component: () => import('./views/Projects.vue') },
  { path: '/awards', component: () => import('./views/Awards.vue') },
  { path: '/adoptions', component: () => import('./views/Adoptions.vue') },
  { path: '/honors', component: () => import('./views/Honors.vue') },
  { path: '/trainings', component: () => import('./views/Trainings.vue') },
  { path: '/export', component: () => import('./views/Export.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
