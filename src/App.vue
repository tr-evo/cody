<template>
  <v-app id="app">
    <!-- Overarching navigation bar -->
    <v-app-bar
      v-if="this.$store.getters.isAuthenticated"
      app
      clipped-right
      dense
      color="white"
      elevation="1"
    >
      <v-toolbar-title>Cody</v-toolbar-title>
      <!-- Navigation Icons -->
      <!-- Auto generate buttons for routes -->

      <v-spacer></v-spacer>

      <v-scroll-x-transition>
        <div 
          v-if="this.$route.name == 'Annotate'"
          class="d-sm-none d-none d-md-flex"
          >
          <v-chip
            class="mx-2"
            color="secondary"
            outlined
            >
              <v-avatar
                v-if="this.$store.state.CRloading == false"
                left
                class="grey lighten-3"
              >
                {{ this.$store.getters.numberCRsug }}
              </v-avatar>
              <v-progress-circular
                v-else
                class="mr-2"
                indeterminate
                color="primary"
                :size="15"
                :width="2"
              ></v-progress-circular>
              Code rule suggestions
          </v-chip>
          <v-chip
            color="secondary"
            outlined>
              <v-avatar
                v-if="this.$store.state.MLloading == false"
                left
                class="grey lighten-3"
              >
                {{ this.$store.getters.numberMLsug }}
              </v-avatar>
              <v-progress-circular
                v-else
                class="mr-2"
                indeterminate
                color="primary"
                :size="15"
                :width="2"
              ></v-progress-circular>
              Learning suggestions
              <v-avatar right><v-icon @click="updateMLannotations">mdi-refresh</v-icon></v-avatar>
              <v-avatar right><v-icon @click="deleteAllMLannotations">mdi-delete</v-icon></v-avatar>
          </v-chip>
        </div>
      </v-scroll-x-transition>

      <v-spacer></v-spacer>

      <!--
      <router-link 
        v-for="route in routersWithoutLogin"
        :to="route"
        :key="route.path"
      >
        <v-btn
        text
        >
          <v-icon left>{{route.icon}}</v-icon><span v-if="$vuetify.breakpoint.name != 'xs'">{{route.name}}</span>
        </v-btn>
      </router-link>
      -->
    </v-app-bar>

    <v-main>
      <div v-if="this.$store.state.serverStatus == 0">
        <v-overlay
          :z-index = "101">
          <v-alert 
            type="error"
            prominent
            :z-index = "102"
            >
            We have trouble connecting to the server right now. Please try to reload the page or try again later, sorry!
          </v-alert>
        </v-overlay>
      </div>
      <!-- Views are inserted here-->
      <transition name="component-fade" mode="out-in" @after-leave="afterLeave">
        <router-view/>
      </transition>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'App',

  components: {
  },

  data: () => ({
  //
  }),

  computed: {
    fileUploaded() {
      if(this.$store.state.inputDocument != null) {
        return true
      }
      else {
        return false
      }
    },

    routersWithoutLogin() {
      const routesDeepCopy = JSON.parse(JSON.stringify(this.$router.options.routes))
      var list = []

      for (let i = 0; i < routesDeepCopy.length; i++) {
        if (!routesDeepCopy[i].name.includes("Log")) {
          list.push(routesDeepCopy[i])
        }
      }
      list.shift()
      return list
    }
  },

  methods: {
    //trigger ML update
    updateMLannotations() {
      this.$store.dispatch('updateMLAnnotations', 'ALL')
    },
    //delete all ML suggestions
    deleteAllMLannotations() {
      this.$store.dispatch('deleteAllMLsuggestions')
    },
    //scrollevent
    afterLeave () {
      this.$root.$emit('triggerScroll')
    },
  },
}

</script>

<style lang="scss">
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a:-webkit-any-link {
    cursor: pointer;
    text-decoration: none;
}

.router-link-exact-active {
    background-color: rgba(0, 0, 0, 0.26);
}

.component-fade-enter-active, .component-fade-leave-active {
  transition: opacity .2s ease;
}
.component-fade-enter, .component-fade-leave-to {
  opacity: 0;
}
</style>
