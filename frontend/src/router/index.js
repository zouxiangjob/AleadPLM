import { createRouter, createWebHistory } from 'vue-router'
import BomTreeTable from '../components/BOMTreeTable.vue'

const routes = [
  { path: '/', component: BomTreeTable }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
