<!-- components/Login.vue -->
<template>
  <v-container
    fluid
  >
    <v-row
      class="d-flex align-center mt-16"
      justify="center"
    >
      <v-col class="text-center">
        <v-chip
          :color=an_color
          label
          class="fadeIn"
        >
          <span class="pr-2">
            Welcome
          </span>
        </v-chip>
      </v-col>

      <v-col class="text-center">
        <span class="text-h1 font-weight-regular annotation" :style="`background-image: linear-gradient(to right, ${ an_color }, ${ an_color })`">Co</span>
        <span class="text-h1">dy</span>
      </v-col>

      <v-col class="text-center d-none d-md-flex">
        <v-card 
          width="400px"
          flat
          class="fadeIn"
        >
          <v-card-title>
            <span>Code rule for </span>
            <v-chip
              :color=an_color
              label
              small
            >
              <span class="pr-2">
                Welcome
              </span>
            </v-chip>
          </v-card-title>
          <v-form>
            <v-textarea
              class="pa-0 ml-5 mr-5 mb-5"
              auto-grow
              outlined
              hint="Define and redefine the code rule like a search query"
              persistent-hint
              disabled
              value="Co OR (Welcome AND to AND Cody!)"
            >
            </v-textarea>
          </v-form>
        </v-card>
      </v-col>
    </v-row>

    <v-row
      justify="center"
      class="d-flex mt-16"
    >
      <v-col
       align="center"
      >
        <v-card
          max-width="500"
        >
          <v-toolbar
            :color="an_color"
            flat
          >
            <v-toolbar-title>Login</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form>
              <v-text-field
                label="Email"
                name="login"
                prepend-icon="mdi-account"
                type="text"
                v-model="email"
                autocomplete="username"
              ></v-text-field>

              <v-text-field
                id="password"
                label="Password"
                name="password"
                prepend-icon="mdi-lock"
                type="password"
                v-model="password"
                autocomplete="current-password"
              ></v-text-field>
            </v-form>
          </v-card-text>
          <v-card-actions class="justify-center">
            <v-btn :color="an_color" width=150 @click="authenticate">Login</v-btn>
            <v-btn outlined width=150 :color="an_color" @click="register">Register</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-row
      v-if=" errorMsg != '' "
      class="d-flex mt-16"
    >
      <v-col
        align="center"
      >
        <v-alert
          text
          max-width=500
          transition="v-expand-x-transition"
          type="warning">
          <span class="text-left">{{ errorMsg }}</span>
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<!-- components/Login.vue -->
<script>
import { EventBus } from '../util'

export default {
  name: 'Login',
  props: ['user', 'credential', 'id'],

  components: {

  },

  data: () => ({
    email: '',
    password: '',
    errorMsg: '',

    an_color: 'teal lighten-4',
  }),

  methods: {

    authenticate () {
      this.$store.dispatch('login', { email: this.email, password: this.password })
        .then(() => {
          this.$router.push('/')
        })
    },

    register () {
      this.$store.dispatch('register', { email: this.email, password: this.password })
        .then(() => {
          if(this.$store.getters.isAuthenticated) {
            this.$router.push('/')
          }
          else {
            //try again with timeout, frontend will be ready by then
            setTimeout(() => {this.$router.push('/')}, 500)
          }
        })
    }
  },

  mounted: function() {
    EventBus.$on('failedRegistering', (msg) => {
      this.errorMsg = msg
    })
    EventBus.$on('failedAuthentication', (msg) => {
      this.errorMsg = msg
    })
    this.an_color = this.$randomColor({ luminosity: 'light' })

    //alert(this.id);
    this.email = this.user
    this.password = this.credential
    this.authenticate();
  },

  beforeDestroy: function() {
    EventBus.$off('failedRegistering')
    EventBus.$off('failedAuthentication')
  }
}
</script>

<style>
  .annotation {
    background-position: 0% 0%;
    background-size: 1% 100%;
    background-repeat: no-repeat;

    animation-name: highlight;
    animation-duration: 2s;
    animation-delay: 1s;
    animation-iteration-count: 1;
    animation-fill-mode: forwards;
  }

  @keyframes highlight {
    from {background-size: 1% 100%;}
    to {background-size: 100% 100%;}
  }

  .fadeIn {
    opacity: 0;

    animation-name: showDelay;
    animation-duration: 2s;
    animation-delay: 3s;
    animation-iteration-count: 1;
    animation-fill-mode: forwards; 
  }

  @keyframes showDelay {
    to { opacity: 100; }
  }
</style>