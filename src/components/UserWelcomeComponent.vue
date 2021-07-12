<template>
  <!-- if now document has been selected yet -->
  <v-container>
    <v-row justify="center" class="mb-6 mt-8">
      <v-col cols="10">
        <h1 class="font-weight-light text-center">Welcome 👋</h1>
        <h3 class="font-weight-light">Looks like you haven't uploaded a document yet, or selected an existing project to work on. You can use the following links to change that! Let us know should you need any assistance with using Cody.</h3>
      </v-col>
    </v-row>
    
    <v-row class="ma-6">
      <v-divider></v-divider>
    </v-row>
    <v-row justify="center">
        <v-col cols="5">
          <v-hover
            v-slot:default="{ hover }"
          >
            <v-card @click="goto('New')" :elevation="hover ? 12 : 2">
              <v-card-title>New document</v-card-title>
              <v-card-subtitle>Get started</v-card-subtitle>
              <v-card-text>Do you want to start a new projet and upload a document. Click here!</v-card-text>
            </v-card>
          </v-hover>
        </v-col>
        <v-col cols="5">
          <v-hover
            v-slot:default="{ hover }"
          >
            <v-card @click="goto('Load')" :elevation="hover ? 12 : 2">
              <v-card-title>Continue your work</v-card-title>
              <v-card-subtitle>Load an existing project</v-card-subtitle>
              <v-card-text>If you have already created a project and want to continue your work, click here!</v-card-text>
            </v-card>
          </v-hover>
        </v-col>
      </v-row>
  </v-container>
  
</template>

<script>
export default {  
  name: 'UserWelcomeComponent',

  data: () => ({
   
  }),

  methods: {
    goto(element) {
      this.$router.push({ name: element})
    },
  },
};
</script>
