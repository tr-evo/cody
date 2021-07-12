<template>
  <!-- Display if document has been selected-->
  <v-container>
    <div @mouseup="saveCoordinates" @click="openMenu">
    
    <!-- Explanation of the input props
      AnnotatedText
        :text="text"  -> The text to be annotated
        :annotations="annotations"  -> The array of annotations
        :getAnnotationColor="getAnnotationColor"  -> Function called to get color value to signal the annotation
        :getSpanClasses="getSpanClasses"  -> function returning CSS classes to apply to the rendered <span> element
        :spanEvents="spanEvents"  -> Event listeners to apply to the <span> elements
        :spanAttributes="spanAttributes"  -> Any HTML attributes to apply to the <span> elements

    -->
      <!-- Display for Text input -->
      <div v-if="this.$store.state.currentDocument.inputType == 0">
        <div v-for="[key, value] of Object.entries(this.document)" 
        :key="key"
        :id="key"
        class="mb-2"
        >
          <div v-for="[attKey, attValue] of Object.entries(value)" 
          :key="attKey"
          :id="attKey"
          >
            <AnnotatedText @editLabelEvent="editLabel"
            :text="attValue"
            :conversation="key"
            :attribute="attKey"
            :annotations="filterAnnotations(key, attKey)"
            :getAnnotationColor="getAnnotationColor"
            :getSpanClasses="getSpanClasses"
            :spanAttributes="spanAttributes"
            />
          </div>
        </div>
      </div>

      <!-- Display for Laddering input -->
      <div v-else-if="this.$store.state.currentDocument.inputType == 1">
        <div v-for="[key, value] of Object.entries(this.document)" 
        :key="key"
        :id="key"
        v-intersect="onIntersect"
        >
          <h2>{{ "Interview #" + key }}</h2>
          <br>
          <div v-for="[attKey, attValue] of Object.entries(value)" 
          :key="attKey"
          :id="attKey"
          >
            <h3>{{ attKey.split('_')[0] }}</h3>
            <br>
            <AnnotatedText @editLabelEvent="editLabel"
            :text="attValue"
            :conversation="key"
            :attribute="attKey"
            :annotations="filterAnnotations(key, attKey)"
            :getAnnotationColor="getAnnotationColor"
            :getSpanClasses="getSpanClasses"
            :spanAttributes="spanAttributes"
            />
            <br>
          </div>
        </div>
      </div>


      <!-- AnnotatedText block is generated for each section of an attribute, therefore loop over conversations and attributes -->
      <div v-else-if="this.$store.state.currentDocument.inputType == 2">
        <div v-for="[key, value] of Object.entries(this.document)" 
        :key="key"
        :id="key"
        v-intersect="onIntersect"
        >
          <h2>{{ key }}</h2>
          <br>
          <div v-for="[attKey, attValue] of Object.entries(value)" 
          :key="attKey"
          :id="attKey"
          >
            <h3>{{ attKey }}</h3>
            <br>
            <AnnotatedText @editLabelEvent="editLabel"
            :text="attValue"
            :conversation="key"
            :attribute="attKey"
            :annotations="filterAnnotations(key, attKey)"
            :getAnnotationColor="getAnnotationColor"
            :getSpanClasses="getSpanClasses"
            :spanAttributes="spanAttributes"
            />
            <br>
          </div>
        </div>
      </div>

    </div>
    <!-- This is the menu that opens for users to select labels for text
      Menu
        :position -> the x and y position of the selection, retreived from the mouseup event
        v-model -> used to reactively display the menu
        absolute -> absolute coordinates since no activator is used

        The functionality of the menu are then added through
          combobox
          overlays
    -->
    <v-menu
        v-model="showMenu"
        :position-x="x"
        :position-y="y"
        :close-on-content-click="false"
        min-width="850px"
        transition="slide-y-transition"
        absolute
        offset-y
    >
      <LabelMenu
          ref="LabelMenu"
          @newLabel="updateDefaultSelection"
          @closeEvent="closeMenu"
          :InputModel="model"
          :currentID="focusAnnotationID"
      />
    </v-menu>

    <v-snackbar
      v-model="snackbar"
      :timeout="3000"
    > 
      {{ snackbar_text }}
      <v-btn
        color="red"
        text
        @click="snackbar = false"
      > Close
      </v-btn>
    </v-snackbar>
  </v-container>
</template>

<script>
  import AnnotatedText from './AnnotatedText.vue';
  import LabelMenu from './LabelMenu.vue';
  import { LightenDarkenColor } from '../util/colorMods'

  export default {
    name: 'TextAnnotationField',
    components: {
      AnnotatedText,
      LabelMenu,
    },

    data: () => ({
      text: "This is a standard text",
      //snackbar
      snackbar: false,
      snackbar_text: 'Annotations across attributes are not allowed so far, sorry.',

      //Menu data
      showMenu: false,
      x: 0,
      y: 0,

      //flag to trigger deletion of focus element once menu is closed
      deletionFlag: false,

      //input in LabelMenu
      model: [],

      //save label id of relevant label
      focusAnnotationID: null,

      defaultColor: '#B0BEC5',

      spanAttributes: null,

      //var to handle deleting "unchanged" default labels when label menu is closed
      lastEditAddDefault: false,

      //array to keep track of visibilities
      convVisibility: {},
      visibilityChanged: true,

      //server Document
      document: {},
    }),

    mounted() {
      //setup visibility array
      let elementsinInput = Object.keys(this.$store.state.inputDocument)
      var firstElement
      for(let element of elementsinInput) {
        //set first element to true (if mounted, first element is visible)
        if(!firstElement) {
           this.convVisibility[element] = true
           firstElement = true
        }
        else {
          this.convVisibility[element] = false
        }
      }

      //trigger chip update once if document consists of one conversation only
      if(Object.keys(this.convVisibility).length == 1) {
        //prevent multiple executions of function, act only when conv-visibility array changed
          window.requestIdleCallback(() => {
            this.$emit('updateChipsOnVisibilityChange', this.convVisibility)
          })
      } 

      //set initial document
      this.document = this.$store.state.inputDocument
    },

    watch: {
      showMenu(val) {
        //remove all values from add label field when menu is closed
        if(val == false) {
          this.model.splice(0, this.model.length)
        }
        //trigger element deletion if flag is true
        if(this.deletionFlag === true) {
          // delete only when input is not availabel (to create a new label)
          if(this.$refs.LabelMenu.search == "" || this.$refs.LabelMenu.search == null) {
            this.$store.dispatch('deleteAnnotation', this.focusAnnotationID)
            this.deletionFlag = false
          }
        }
      },
    },

    computed: {
      //list of current annotations
      annotations() {
        return this.$store.state.annotations
      },
    },

    methods: {
      getAnnotationColor: function(annotation) {
        const color = this.$store.state.codes.filter( code => {
          return code["text"] === annotation.label
        })
        //if label is new, provide default color
        if(color.length === 0) {
          return this.defaultColor
        }
        //if annotation is recommendation, make color lighter using function from colorMods util
        else if(annotation.isRecommendation == 1) {
          return LightenDarkenColor(color[0]["color"], 40)   // Must return hex value
        }
        else {
          return color[0]["color"]  // Must return hex value
        }
      },

      getSpanClasses: function(span) {
        const classes = ['annotation-span']
        const annotationIds = span.annotationIds
        if (annotationIds.length > 0) {
          classes.push('annotated')
        }
        return classes
      },

      saveCoordinates() {
        var boundaryRect = window.getSelection().getRangeAt(0).getBoundingClientRect()
        //only change x/y when labelMenu is not showing
        if(this.showMenu == false) {
          this.x = boundaryRect.x
          this.y = boundaryRect.y + boundaryRect.height
        }
      },

      openMenu(e) {
        e.preventDefault()
        if(this.saveSelection()) {
          this.showMenu = false
          this.$nextTick(() => {
            if(this.$refs.LabelMenu != undefined) {
              this.$refs.LabelMenu.model.pop()
            }
            this.showMenu = true
          })
        } else {
          //delete default selection if menu is closed without changing default label
          if(this.lastEditAddDefault == true) {
            this.deletionFlag = true
            this.lastEditAddDefault = false
          }
        }
      },

      saveSelection() {
        var selObj = document.getSelection();

        //prevent that user makes selections accross attributes / conversations by checking if anchor and focus are in the same overarching span (dont need to bother for text, since there the overarching parent is the same for the entire field)
        var parentOfAnchor = selObj.anchorNode.parentNode.parentNode
        var parentOfFocus = selObj.focusNode.parentNode.parentNode

        if(parentOfAnchor != parentOfFocus) {
          document.getSelection().collapseToStart();
          this.snackbar = true
        }

        var selectionAdded = false;
        //dont do anything if selection is empty
        if(!selObj.isCollapsed) {
          //build object for new annotation
          var newAnnotation = {
            conversation: null,
            attribute: null,
            annotationID: null,
            id: null,
            start: null,
            length: null,
            label: null
          }
         
          //fill annotation object properties
          //take selection string as ID for now
          newAnnotation.id = selObj.toString();
          //get id of node for current selection with JS based on span-ID
          var selectionNodeID = selObj.anchorNode.parentNode.getAttributeNode("data-span-id").value;

          //#make selection based on unit-of-analysis settings
          //Free form
          if(this.$store.state.currentDocument.uoa == 0) {
            //loop through previous siblings and add length to calculate start value of selection
            var startValue = 0;
            var nodeList = selObj.anchorNode.parentNode.parentNode.childNodes;

            for(var i = 0; i < selectionNodeID; i++) {
              startValue += nodeList.item(i).textContent.length
            }
            //add length from start of node to anchor (start) / control if selection contains another node
            //other node contained
            if(selObj.anchorNode != selObj.focusNode) {
              //annotation from left to right
              //annotation from right to left
              selObj.anchorOffset < selObj.focusOffset ? startValue += selObj.focusOffset : startValue += selObj.anchorOffset
            }
            //no node contained
            else {
              //prevent case where anchor is right of focus (user selected from right to left)
              selObj.anchorOffset > selObj.focusOffset ? startValue += selObj.focusOffset : startValue += selObj.anchorOffset
            }
            
            //set start of selection object
            newAnnotation.start = startValue;
           
            //set length to length of selection text
            newAnnotation.length = selObj.toString().length;
          }

          //Paragraph selection
          else if(this.$store.state.currentDocument.uoa == 1) {
            //get string of anchorBlock and split into substrings on \n\n
            var text = selObj.anchorNode.parentNode.parentNode.innerText.split("\n\n")
            //find paragraph the contains selection
            var index = this.paragraph_identifyBlock(text, newAnnotation.id)

            //set start of selection object
            var startValue2 = 0
            for(var a = 0; a < index; a++) {
              startValue2 += text[a].length + 2 //add 2 characters for 2 * \n elements that have been filtered out
            }

            newAnnotation.start = startValue2;
           
            //set length to length of selection text
            newAnnotation.length = text[index].length;

            //set text to be saved for annotation (id) to entire text of section
            newAnnotation.id = text[index]
          }

          //Sentence selection - not implemented as of now
          else {
            null
          }

          //set class of new selection, tool as prototype for now
          newAnnotation.label = 'default'

          //get conversation and attribute [lots of parentNode accessing]
          newAnnotation.attribute = selObj.anchorNode.parentNode.parentNode.parentNode.id
          newAnnotation.conversation = selObj.anchorNode.parentNode.parentNode.parentNode.parentNode.id

          //set annotationID
          newAnnotation.annotationID = newAnnotation.conversation.charAt(0) + '-' + newAnnotation.attribute.charAt(0) + '-' + newAnnotation.start + '-' + newAnnotation.length + '-' + (Math.floor(Math.random() * Math.floor(10000)))
            
          //push annotation to data object
          this.$store.dispatch('addAnnotation', newAnnotation).then((res) => {
            //set pointer to relevant label
            this.focusAnnotationID = res
          })
          selectionAdded = true;
          newAnnotation = null;

          //let component know the last added element is a 'default'
          this.lastEditAddDefault = true
        }
        //remove selection
        selObj.empty();

        return selectionAdded;
      },

      //update relevant label with information for LabelMenu
      updateDefaultSelection(payload) {
        //let component know that default element is to be kept
        this.lastEditAddDefault = false
        //if deleting option is called
        if(payload[0] === "delete") {
          this.deletionFlag = true
        }
        else {
          //remove deletion flag
          this.deletionFlag = false
          //update the existing annotation / payload: [labelClass, labelColor]
          //the payload contains all remaining labels for the current span, check if payload length == number of annotations for that span
          let annotationIDParts = this.focusAnnotationID.split('-')
          let annotationIDwithoutRandom = annotationIDParts[0] + "-" + annotationIDParts[1] + "-" + annotationIDParts[2] + "-" + annotationIDParts[3]
          let annotationsForSpan = this.$store.state.annotations.filter( an => an.annotationID.startsWith(annotationIDwithoutRandom))
          //filter for labels being added or removed
          //case deletion: less labels in payload than annotations for span
          if(payload.length < annotationsForSpan.length) {
            //identify annotations to be deleted
            let annotationsToDelete = annotationsForSpan.filter( an => !payload.some( label => label.text == an.label ))
            //delete annotations
            for(let an of annotationsToDelete) {
              this.$store.dispatch('deleteAnnotation', an.annotationID)
            }   
          }

          //case addition: more labels in payload than annotations for span
          else if(payload.length > annotationsForSpan.length) {
            //identify the new label(s)
            let newLabel = payload.filter( label => !annotationsForSpan.some( an => an.label === label.text ))
            //add new annotations for these labels
            //get base data of current span to create new annotation
            let currentAnnotation = this.$store.state.annotations.filter( an => an.annotationID === this.focusAnnotationID)[0]
            var newAnnotation = {
              conversation: currentAnnotation.conversation,
              attribute: currentAnnotation.attribute,
              annotationID: currentAnnotation.conversation.charAt(0) + '-' + currentAnnotation.attribute.charAt(0) + '-' + currentAnnotation.start + '-' + currentAnnotation.length + '-' + (Math.floor(Math.random() * Math.floor(10000))),
              id: currentAnnotation.id,
              start: currentAnnotation.start,
              length: currentAnnotation.length,
              label: null
            }
            for(let l of newLabel) {
              newAnnotation.label = l.text
              // prevent trigger if label is empty
              if(newAnnotation.label != "") {
                this.$store.dispatch('addAnnotation', newAnnotation)
              }
            }
          }

          //case update: same number of labels in payload than annotations for span -> when default label is changed into first actual label
          else {
            let labelText = typeof payload[0] === 'object' ? payload[0].text : payload[0]
            //prevent update of label if label is empty
            if(labelText != "") {
              this.$store.dispatch('updateAnnotationLabel', [this.focusAnnotationID, labelText])
            }
          }          
        }
      },

      editLabel(payload) {
        //let component know that default element is to be kept
        this.lastEditAddDefault = false
        //based on x,y position of click (x - 250: half size of label menu) (y + 10 so we prevent direct overlap)
        this.x = payload[0].clientX - 250
        this.y = payload[0].clientY + 10

        //open menu
        this.showMenu = false
        this.$nextTick(() => {
          this.showMenu = true
        })
        //add current label(s) to model so it appears in input field
        var spanInfo = payload[1]
        let currentLabels = []
        if(spanInfo[0] != undefined) {
          for(let element of spanInfo) {
            currentLabels.push(
            {
              text: element.label,
              color: this.getAnnotationColor(element)
            })
          }
        }

        //set pointer to relevant label
        this.focusAnnotationID = payload[1][0].annotationID
        
        //edit model array only if the currently contained node is != currentLabel
        //add all labels for the current span to the model for LabelMenu
        if(JSON.stringify(currentLabels) != JSON.stringify(this.model)) {
          for(let el of currentLabels) {
            this.model.push(el)
          }
          //this.model.length = this.model.length < 2 ? this.model.length : 1
        }
      },

      filterAnnotations(conv, attr) {
        //visibility value of current conversation
        const annotationVisible = this.convVisibility[conv.toString()]
        //only in here to trigger recalculation of method when this.visibilityChanged changes
        if(this.visibilityChanged);
        return this.annotations.filter((an) => {
          if(an.conversation == conv && an.attribute == attr && annotationVisible == true) {
            return true
          }
        })
      },

      paragraph_identifyBlock(blocks, selectionText) {
        //split in words
        var textblocks = selectionText.split(" ")
        //count how many of the textblocks are contained in each block and save in array
        var counts = []
        let count = 0

        for(var block of blocks) {
          count = 0
          for(var text of textblocks) {
            block.includes(text) ? count++ : null
          }
          counts.push(count)
        }
        return counts.indexOf(Math.max(...counts))
      },

      closeMenu() {
        this.showMenu = false
      },

      onIntersect(entries) {
        //update visibility array
        let targetID = entries[0].target.id
        this.convVisibility[targetID] = entries[0].isIntersecting
        this.visibilityChanged = !this.visibilityChanged
        if(entries[0].isIntersecting == false) {
          //prevent multiple executions of function, act only when conv-visibility array changed
          window.requestIdleCallback(() => {
            this.$emit('updateChipsOnVisibilityChange', this.convVisibility)
          })
        }
      },
    }
  };
</script>

<style>
  .annotated {
    font-weight: bold;  
  }

  .v-menu__content {
    webkit-box-shadow: none;
    box-shadow: none;
  }

  .annotation-span {
    white-space: pre-wrap;
  }
</style>