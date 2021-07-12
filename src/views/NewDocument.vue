<template>
  <v-container>
    <v-row justify="center" class="mb-6 mt-8">
      <v-col cols="10">
        <h1 class="font-weight-light text-center">Create a new document ✨</h1>
        <h3 class="font-weight-light text-center">Just follow the three steps!</h3>
      </v-col>
    </v-row>

    <v-overlay
      :absolute="true"
      :value="overlay"
      :opacity="0.8"
    >
      <v-container>
        <v-row justify="center" class="mb-10"><span>Document is being uploaded and processed. This shouldn't take long.</span></v-row>
        <v-row justify="center"><v-progress-circular
          color="white"
          :size="50"
          indeterminate
        >
        </v-progress-circular></v-row>
      </v-container> 
    </v-overlay>

    <v-row justify="center" class="mt-12">
      <v-col md="10">
        <v-stepper v-model="step" vertical>
          <v-stepper-step :complete="step > 1" step="1" editable>
            Provide a name for the document
            <small>Summarize if needed</small>
          </v-stepper-step>

          <v-stepper-content step="1">
            <v-sheet width="60%">
              <v-text-field 
                clearable 
                label="Name" 
                v-model="name" 
                :rules="[rules.required]"
                @blur="(name == '' ? step = 1 : step = 2)"
                @keydown.enter="$event.target.blur()"
                ></v-text-field>
            </v-sheet>
          </v-stepper-content>

          <v-stepper-step :complete="step > 2" step="2" editable>
          Upload a document
          </v-stepper-step>

          <v-stepper-content step="2">
            <v-sheet width="60%">
              <v-file-input
              small-chips
              show-size
              color=undefined
              label="Select a file from your computer"
              v-model="file"
              @change="processFile"
              >
              </v-file-input>
            </v-sheet>
          </v-stepper-content>

          <v-stepper-step :complete="step > 3" step="3" editable>
          Adjust the settings for this document
          </v-stepper-step>

          <v-stepper-content step="3">
            <v-container>
              <v-row align="center" justify="start">
                <v-col md="4">
                  <span>Type of document</span>
                </v-col>
                <v-col>
                  <v-btn-toggle v-model="type_selection_exclusive">
                    <v-btn outlined>Text</v-btn>
                    <v-btn outlined>Laddering</v-btn>
                    <v-btn outlined>LadderBot</v-btn>
                  </v-btn-toggle>
                </v-col>
              </v-row>
             
              <v-row align="center" justify="start">
                 <v-col md="4">
                  <span>Unit-of-analysis</span>
                </v-col>
                <v-col>
                  <v-btn-toggle v-model="unit_of_analysis">
                    <v-btn outlined>Free form</v-btn>
                    <v-btn outlined>Paragraph</v-btn>
                  </v-btn-toggle>
                </v-col>
              </v-row>

              <v-row justify="center" class="mt-12">
                <v-col md="auto">
                  <v-btn color="primary" @click="submit">Continue</v-btn>
                </v-col>
                <v-col md="auto">
                  <v-btn text @click="step = 1">Cancel</v-btn>
                </v-col>
              </v-row>
            </v-container>
          </v-stepper-content>
        </v-stepper>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'NewDocument',

  components: {
  },

  data: () => ({
    step: 1,
    name: null,
    file: null,
    processedInput: null,
    type_selection_exclusive: null,
    unit_of_analysis: null,

    //show overlay
    overlay: false,

    rules: {
      required: value => !!value ||'Required.',
    },
  }),

  computed: {
    hasError() {
      return (this.name == null || this.file == null || this.type_selection_exclusive == null)
    },

    serverDocuments() {
      return this.$store.state.serverDocuments
    }
  },

  watch: {
    serverDocuments: function(now, prev) {
      if(now.length != prev.length) {
        this.$router.push('/')
      }
    },
  },

  methods: {
    submit() {
      //proceed with submit only if all detail have been provided
      if(!this.hasError) {
        //load text first to get processed string ||MIGHT CHANGE TO PROCESSING ON SERVER LATER
        const v = {
          name: this.name,
          settings: {
            type: this.type_selection_exclusive,
            uoa: this.unit_of_analysis,
          },
          content: this.processedInput,
        }
        this.overlay = true
        this.$store.dispatch('newDocument', v)
      }
    },

    processFile() {
      if(this.file == null) {
        this.step = 2
      }
      else {
        const reader = new FileReader();

        reader.onload = (e) => { 

          let inputText = e.target.result;
          //react to different types of input
          let processedInput = null

          try {
            //if json
            processedInput = JSON.parse(inputText);
          }
          catch(err) {
            window.console.log("FileInput: Input not of type .json, trying .txt next")
            processedInput = inputText
          }
          //write text in data for bundled dispatch
          this.processedInput = processedInput
        }
        if(this.file != null) {
          reader.readAsText(this.file)
        }

        this.step = 3
        }
    },
  },
};
</script>
