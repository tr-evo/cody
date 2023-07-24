import Vue from 'vue'
import VueRouter from 'vue-router'

import Login from '../views/Login.vue'
import Home from '../views/Home.vue'
import Analytics from '../views/Analytics.vue'
import NewDocument from '../views/NewDocument.vue'
import Documents from '../views/Documents.vue'
import store from '@/store'

Vue.use(VueRouter)

const routes = [
    {
    path: '/login/:user/:credential/:id',
    name: 'LoginParams',
    component: Login,
    props: true,
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/new',
    name: 'New',
    component: NewDocument,
    icon: 'mdi-plus-box-multiple',
    beforeEnter (to, from, next) {
      if (!store.getters.isAuthenticated) {
        next('/login')
      } else {
        next()
      }
    }
  },
  {
    path: '/',
    name: 'Load',
    component: Documents,
    icon: 'mdi-text-box-multiple-outline',
    beforeEnter (to, from, next) {
      if (!store.getters.isAuthenticated) {
        next('/login')
      } else {
        next()
      }
    }
  },
  {
    path: '/document',
    name: 'Annotate',
    component: Home,
    icon: 'mdi-file-document-edit-outline',
    beforeEnter (to, from, next) {
      if (!store.getters.isAuthenticated) {
        next('/login')
      } else {
        next()
      }
    }
  },
  {
    path: '/anx',
    name: 'Analyze',
    component: Analytics,
    icon: 'mdi-google-analytics',
    beforeEnter (to, from, next) {
      if (!store.getters.isAuthenticated) {
        next('/login')
      } else {
        next()
      }
    }
  },
  {
    path: '/logout',
    name: 'Logout',
    component: Login,
    icon: 'mdi-logout-variant',
    beforeEnter (to, from, next) {
      //remove jwt to logout user
      store.state.jwt = ''
      //send user to login page
      next('/login')
    }
  }
]

// scrollBehavior:
// - only available in html5 history mode
const scrollBehavior = function() {
  let position = { x: 0, y: 0 }

  return new Promise(resolve => {
    // wait for the out transition to complete (if necessary)
    this.app.$root.$once('triggerScroll', () => {
      resolve(position)
    })
  })
}

const router = new VueRouter({
  routes, scrollBehavior
})

export default router
