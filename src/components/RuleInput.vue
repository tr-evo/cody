<template>
  <v-card 
    width="400px"
    :elevation="5"
  >
    <v-card-title>
      <span>Code rule for </span>
      <v-chip
      v-for="label in model"
      :key="label.text"
      :color="label.color"
      label
      small
      @click="loadNewRule(label)"
      >
        <span class="pr-2">
          {{ label.text }}
        </span>
      </v-chip>
      <v-chip
        v-if="model.length == 0"
        label
        small
        color="grey"
      >
        <span class="pr-2">Please select a label</span>
      </v-chip>
    </v-card-title>
    <v-form
      v-model="form"
    >
      <v-textarea
        class="pa-0 ml-5 mr-5 mb-5"
        auto-grow
        outlined
        persistent-hint
        label="Edit code rule here"
        v-model="input"
        :hint="hint"
        :rules="[rules.code]"
        @input="notifyUser"
        :loading="isLoading"
        :disabled="disabled"
      >
        <template v-slot:append-outer>
          <v-icon v-if="status == null">mdi-dots-horizontal</v-icon>
          <v-icon v-else-if="status == 0" @click="updateRule(input)">mdi-content-save-outline</v-icon>
          <v-icon v-else>mdi-check-outline</v-icon>
        </template>
      </v-textarea>
    </v-form>
   
    <div v-if="currentAnnotation != null">
      <v-card-text 
        v-if="currentAnnotation.matchHighlight != null" 
        class="pt-0"
      >
        <v-container fluid class="py-0">
          <v-row 
            align="center"
            justify="start"
          >
            <v-col cols="1" class="px-0 pt-1">
              <v-icon>mdi-lightbulb-on-outline</v-icon>
            </v-col>
            <v-col cols="11" class="px-0 pt-1">
              <p v-if="currentAnnotation.confidence == 1.0" class="mb-0 text-body-2">
                Cody suggests this label because it matches a code rule</p>
              <p v-else class="mb-0 text-body-2">
                Cody suggests this label because it seems to contain a relevant word</p>
            </v-col>
          </v-row>
        </v-container>
       
        <p v-if="currentAnnotation.confidence == 1.0" class="mb-1">This section contains the following <b>keywords</b>:</p>
        <p v-else class="mb-1">Your previous annotations with this label commonly contain the word(s):</p>
        <v-divider></v-divider>
        <p class="mt-2" v-html="currentAnnotation.matchHighlight"></p>
      </v-card-text>
    </div>
  </v-card>
</template>

<script>
export default {  
  name: 'RuleInput',
  props: {
      //prop for referencing the currently selected label
      model : {
        type: Array,
        default: function() {
          return []
        },
      },
      currentID: String,
    },

  data: () => ({
    rules: {
      code: v => {
        if(v != undefined) {
          const regex = / AND | and | OR | or | NOT | not |\(|\)/gm
          const trimmed = v.trim()
          const splitString = trimmed.split(regex)
          for (let a of splitString) {
            //if whitespace is found, then multiple words are inbetween delimiters
            //control for whitespace in between strings in quotes " … "
            if(a.indexOf(' ') >= 0 && a.startsWith('"') == false) return 'Use AND, OR, NOT and brackets to combine multiple search terms. Two or more words need to be "in quotation marks".'
          }
          //if no whitespace is present, than form is correct
          return true
        }
        else return true
        
      }
    },
    //current input value based on server
    input: "…",
    //flag to enable saving when rules are fullfilled
    form: false,
    //flag to display if change to code rule has been saved
    changeSaved: false,
    //flag for loading status when code rule is fetched
    isLoading: false,
    //currently selected label
    labelInFocus: null,
    //status icon :: null - no label selected, 0 - changes unsaved, 1 - changes saved
    status: null,
    //hint to guide user
    hint: "Define and redefine the code rule like a search query"
   
  }),

  computed: {
    currentAnnotation() {
      //two routes to enable highlight recalculation when other label is selected
      let annotation = null
      let id_part = null
      if(this.labelInFocus != null) {
        //split id string into first four parts -> only random number is different for multiple annotations for one section
        id_part = this.currentID.split("-", 4)
        //join them back together
        id_part = id_part.join('-')
        annotation = this.$store.state.annotations.find(an => an.annotationID.startsWith(id_part) && an.label === this.labelInFocus.text)
      }
      else {
        annotation = this.$store.state.annotations.find(an => an.annotationID === this.currentID)
      }
      
      if(annotation != undefined) {
        return annotation
      }
      else {
        return null
      }
    },

    disabled() {
      return (this.labelInFocus == null || this.labelInFocus.text == 'default')
    },
  },

  watch: {
    model(val) {
      //when currently relevant label changes, retrieve relevant code rule from server
      if(val.length > 0 && val[0].text != 'default' && val[0].text != '') {
        this.isLoading = !this.isLoading
        this.$store.dispatch('getCodeRule', val[0].text).then(() => {
          this.input = this.$store.state.codeRule
          this.isLoading = !this.isLoading
          this.status = 1
        })
      }
      else {
        this.input = "…"
        this.status = null
      }
      this.labelInFocus = this.model[0]
    },
  },

  methods: {
    updateRule(payload) {
      if(this.form == true) {
        this.$store.dispatch('updateCodeRule', [this.labelInFocus.text, payload]).then(() => {
          this.isLoading = !this.isLoading
          this.$store.dispatch('getCodeRule', this.labelInFocus.text).then(() => {
            this.input = this.$store.state.codeRule
            this.isLoading = !this.isLoading
            this.status = 1
            this.hint = "Define and redefine the code rule like a search query"
          })
        })
      }
    },

    loadNewRule(label) {
      if(label.text != undefined) {
        //change model in focus
        this.labelInFocus = label
        if(label.text.length > 0 && label.text != 'default' && label.text != '') {
          this.isLoading = !this.isLoading
          this.$store.dispatch('getCodeRule', label.text).then(() => {
            this.input = this.$store.state.codeRule
            this.isLoading = !this.isLoading
            this.status = 1
          })
        }
      }
      else {
        this.input = "…"
      }
    },

    notifyUser() {
      this.hint = "Click the disk to save your changes and generate new label suggestions"
      this.status = 0
    },
  },
};
</script>

<style>

b {
  color: #009688;
}

</style>
