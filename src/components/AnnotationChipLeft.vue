
<template>

  <div
    :style="style"
  >
    <v-chip
      :color="labelColor"
      label
      small
      @click="chipClicked"
      class="max-width-chip"
    >
      <span class="pr-2">
        {{ label }}
      </span>
    </v-chip>
    <br/>
    <!-- Adjust chip based on number of labels available for this span | Chip for one label -->
    <v-chip
      color="teal lighten-5"
      label
      small
      v-if="confidence != undefined && annotationsForSpan === 1"
    >
  
      <v-icon left>mdi-face-agent</v-icon>
      <v-icon left>mdi-lightbulb-on-outline</v-icon>

      <span class="pr-2" @click="chipClicked">
        {{ parseFloat(confidence).toFixed(2) * 100 + "%"}}
      </span>
      <v-avatar right><v-icon @click="acceptAnnotation">mdi-check</v-icon></v-avatar>
      <v-avatar right><v-icon @click="deleteAnnotation">mdi-delete</v-icon></v-avatar>
    </v-chip>
    
    <!-- Chip for multiple suggestions / labels available -->
    <v-chip
      color="teal lighten-5"
      label
      small
      v-else-if="confidence != undefined && annotationsForSpan > 1"
    >
  
      <v-icon left>mdi-face-agent</v-icon>
      <v-icon left>mdi-flash-outline</v-icon>

      <v-chip
        color="#ebb5ae"
        label
        small
        >
        {{ "[" + (annotationsForSpan - 1) + "] alternative(s)" }}
      </v-chip>
    </v-chip>
  </div>

</template>

<script>
export default {  
  name: 'AnnotationChipLeft',

  props: ['annotationID', 'label', 'confidence'],

  data: () => ({
    style: "",
  }),

  mounted() {
    this.style = "position: absolute; top: " + this.getElementPosY() + "px; left: 20px; max-width: " + this.$parent.$refs.ChipsCol.offsetWidth + "px;"
  },

  beforeUpdate() {
    this.style = "position: absolute; top: " + this.getElementPosY() + "px; left: 20px; max-width: " + this.$parent.$refs.ChipsCol.offsetWidth + "px;"
  },

  computed: {
    labelColor() {
      try {
        let element = this.$store.state.codes.find( code => code.text == this.label )
        return element.color
      }
      catch {
        return null
      }
    },

    annotationsForSpan() {
      //filter by annotationID, return list of all labels where related annotation id starts with this.annotationID
      let filterlist = this.$store.state.annotations.filter( an => an.annotationID.startsWith(this.shortenedID(this.annotationID)))
      return filterlist.length
    },
  },

  methods: {
    getElementPosY() {
      try {
        let element = document.getElementById(this.annotationID)
        //if element cant be found because ID changed when annotating over an existing annotation 
        if(element == null) {
          return -999
        }
        //12: height of half the chip, 24: height of the top app bar, window.scrollY: current scroll to account for labels added later when user has scrolled
        //when two chips are used (= label and recommendation) subtract another 12 px (half the chip size) to get appropriate positioning
        if(this.confidence == undefined) {
          return (element.getBoundingClientRect().top + (element.getBoundingClientRect().height / 2 - 12 - 48) + window.scrollY)
        }
        else {
          return (element.getBoundingClientRect().top + (element.getBoundingClientRect().height / 2 - 12 - 48) + window.scrollY - 12)

        }
      }
      catch(e) {
        return -999
      }
    },

    chipClicked(e) {
      const annotations = this.$store.state.annotations.find(an => an.annotationID == this.annotationID)
      this.$emit('chipClicked', [e, [annotations]])
    },
    //get shortenedID to identify multiple automated annotations for one span
    shortenedID(annotationID) {
      let an = this.$store.state.annotations.find(an => an.annotationID == annotationID)
      return an.conversation.charAt(0) + '-' + an.attribute.charAt(0) + '-' + an.start + '-' + an.length
    },
    //accept attached annotation
    acceptAnnotation() {
      this.$store.dispatch('changeMLtoManual', this.annotationID)
    },
    //delete attached annotation
    deleteAnnotation() {
      this.$store.dispatch('deleteAnnotation', this.annotationID)
    }
  },
};
</script>

<style>
.max-width-chip.v-chip {

}

.max-width-chip .v-chip__content {
  line-height: 24px;
  display: inline-block !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
