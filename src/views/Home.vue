<template>
  <!-- if no document has been selected yet -->
  <div v-if="this.$store.state.currentDocument == null">
    <UserWelcomeComponent />
  </div>

  <!-- if document has been selected -->
  <div v-else>
    <!-- Signal that document is loading -->
    <v-overlay
      :value="overlay"
      :opacity="0.8"
    >
      <v-container>
        <v-row justify="center" class="mb-10"><span>Loading your document, hang tight.</span></v-row>
        <v-row justify="center"><v-progress-circular
          color="white"
          :size="50"
          indeterminate
        >
        </v-progress-circular></v-row>
      </v-container> 
    </v-overlay>

    <v-container fluid>
      <v-row>
        <v-col
          ref="ChipsCol"
          cols="2"
          sm="3"
          lg="2"
          >
          <AnnotationChipLeft
            ref="AnnotationChips"
            @chipClicked="startEditing"
            v-for="an in uniqueAnnotations"
            :key="an.annotationID"
            :annotationID="an.annotationID"
            :label="an.label"
            :confidence="an.confidence"
          >
          </AnnotationChipLeft>
        </v-col>
        <v-col
          cols="10"
          sm="8"
          lg="9"
          >
          <TextAnnotationField 
            ref="TextAnnotationField"
            @updateChipsOnVisibilityChange="forceChipUpdate">
          </TextAnnotationField>
        </v-col>
        <v-col
          v-if="$vuetify.breakpoint.name != 'xs'"
          cols="auto"
          >
          <CodebookDrawer/> <!-- updateLabelPositions -->
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import TextAnnotationField from '../components/TextAnnotationField'
import CodebookDrawer from '../components/CodebookDrawer'
import AnnotationChipLeft from '../components/AnnotationChipLeft'
import UserWelcomeComponent from '../components/UserWelcomeComponent'

export default {
  name: 'Home',

  components: {
    TextAnnotationField,
    CodebookDrawer,
    AnnotationChipLeft,
    UserWelcomeComponent,
  },

  data: () => ({
    show: true,
    //snapshot of visibility to prevent exessive updating
    visibilitySnapshot: []
  }),

  //preserve scrolling on exit
  beforeRouteLeave (to, from, next) {
      this.$store.dispatch('documentScrollPosition', { x: window.scrollX, y: window.scrollY })
      next()
  },

  //write scrolling position on next enter
  beforeRouteEnter (to, from, next) {
    next(vm => {
      // access to component instance via `vm`
      window.scrollTo(vm.$store.state.documentScroll.x, vm.$store.state.documentScroll.y)
    })
  },

  computed: {
    //array with only one annotation per span
    uniqueAnnotations: function() {
      let annotations = this.$store.state.annotations
      let uniqueArray = []
      let chipList = []
      for(let an of annotations) {
        let ID = an.annotationID
        if(!chipList.includes(ID)) {
          chipList.push(ID)
          uniqueArray.push(an)
        }
      }
      //return only those chips where the related annotation is currently visible
      return uniqueArray.filter( chips => this.visibilitySnapshot[chips.conversation.toString()] == true )
      //return uniqueArray
    },

    overlay() {
      return this.$store.state.isLoading
    }
  },

  watch: {
    '$vuetify.breakpoint.name': function() {
      for(let chip of this.$refs.AnnotationChips) {
        chip.$forceUpdate()
      }
    }
  },

  methods: {
    startEditing(payload) {
      this.$refs.TextAnnotationField.editLabel(payload)
    },

    forceChipUpdate(payload) {
      //prevent that forceUpdate is called if no chips exist
      if(this.$refs.AnnotationChips != undefined) {
        //if payload equals snapshot, prevent update
        if(JSON.stringify(payload) != JSON.stringify(this.visibilitySnapshot)) {
          // change snapshot to trigger update of chips which use the snapshot to (re)calculate visibility
          this.visibilitySnapshot = JSON.parse(JSON.stringify(payload))
        }
      }
      else {
        this.visibilitySnapshot = JSON.parse(JSON.stringify(payload))
      }
    },
  },
};
</script>
