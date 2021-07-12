import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify';
import 'material-design-icons-iconfont/dist/material-design-icons.css';
import VueRandomColor from 'vue-randomcolor'
import vuescroll from 'vue-scroll'
import store from './store'
import router from './router'
import VueSSE from 'vue-sse'

Vue.config.productionTip = false
Vue.use(VueRandomColor)
Vue.use(vuescroll)
Vue.use(VueSSE)

new Vue({
  vuetify,
  store,
  router,
  render: h => h(App)
}).$mount('#app')
