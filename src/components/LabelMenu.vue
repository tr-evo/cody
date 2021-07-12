<template>
  <v-container fluid>
    <v-combobox @change="forwardChange" @[updateEvent]="listIndexChanged"
      ref="combobox"
      v-model="model"
      :filter="filter"
      :hide-no-data="!search"
      :items="items"
      :search-input.sync="search"
      hide-selected
      label="Search for a label or create one"
      small-chips
      solo
      multiple
      autofocus
      prepend-inner-icon="close"
      @[closeEvent]="closeInput"
    >

      <template v-slot:no-data>
        <v-list-item>
          <span class="subheading">Press <kbd>enter</kbd> to create the code </span>
          <v-chip
            :color="nextColor"
            label
            small
          >
            {{ search }}
          </v-chip>
        </v-list-item>
      </template>

      <template v-slot:selection="{ attrs, item, parent, selected }">
        <v-chip
          v-if="item === Object(item)"
          v-bind="attrs"
          :color="`${item.color}`"
          :input-value="selected"
          label
          small
        >
          <span class="pr-2">
            {{ item.text }}
          </span>
          <v-icon
            small
            @click="parent.selectItem(item)"
          >close</v-icon>
        </v-chip>
      </template>

      <template v-slot:item="{ index, item }">
        <v-text-field
          v-if="editing === item"
          v-model="editing.text"
          :placeholder = "placeholder"
          autofocus
          flat
          background-color="transparent"
          hide-details
          solo
          @keyup.enter.stop.prevent="edit(index, item)"
          @click.stop.prevent
        ></v-text-field>
        <v-chip
          v-else
          :color="`${item.color}`"
          label
          small
        >
          {{ item.text }}
        </v-chip>
        <v-spacer></v-spacer>
        <v-list-item-action @click.stop>
          <v-btn
            icon
            @click.stop.prevent="edit(index, item)"
          >
            <v-icon>{{ editing !== item ? 'mdi-pencil' : 'mdi-check' }}</v-icon>
          </v-btn>
        </v-list-item-action>
      </template>

      <template v-slot:append-outer>
        <RuleInput 
          class="mt-n3"
          :model="model"
          :currentID="currentAnnotationID"
        >
        </RuleInput>
      </template>

    </v-combobox>
  </v-container>
</template>

<script>
import RuleInput from './RuleInput.vue'

  export default {
    components: {
      RuleInput
    },

    props: {
      //prop for setting the model = content of input field from parent component
      InputModel : {
        type: Array,
        default: function() {
          return []
        },
      },
      currentID: String,
    },

    data: () => ({
      activator: null,
      attach: null,
      nextColor: null,
      editing: null,
      //save label when editing starts
      editingOldItem: null,

      //placeholder for label edits
      placeholder: "You are about to delete this label!",

      index: -1,
      model: [],
      x: 0,
      search: null,
      y: 0,

      //check if current filter returns empty list
      updateEvent: 'update:list-index',
      listIndex: -1,
      preventNextInput: false,

      //check status of menu
      closeEvent: 'click:prepend-inner',
    }),

    mounted: function() {
      //options: https://github.com/davidmerfield/randomColor#options
      this.nextColor = this.$randomColor({ luminosity: 'light' })
      if(this.InputModel.length != 0) {
        for(let el of this.InputModel) {
          this.model.push(el)
        }
      }
    },

    computed: {
      items() {
        return JSON.parse(JSON.stringify(this.$store.state.codes))
      },

      currentAnnotationID() {
        return this.currentID
      },

    },

    watch: {
      model (val, prev) {
        if (val.length === prev.length) return

        //when model changes, end every editing process
        if(this.editing) {
          // ===> if editing is active and current label is empty and edit is not called -> undo if possible :: refresh state.codes
          this.editing.text = this.editingOldItem.text
          this.editing = null
          this.index = -1
          this.editingOldItem = null
        }

        //prevent that two new codes are added to model at the same time
        this.search = null

        this.model = val.map(v => {
          if (typeof v === 'string') {
            if(this.listIndex == -1) {
              v = {
                text: v,
                color: this.nextColor,
              }
              //add code only if it does not exist yet
              if((this.items.find(code => code.text === v.text)) == undefined) {
                this.$store.dispatch('addCode', v)
              }
              this.nextColor = this.$randomColor({ luminosity: 'light' })
            }
          }
          //return current v only if it is not a string anymore
          if(typeof v != 'string') {
            return v
          }
        })
      },

      InputModel(val) {
        //prevent action if InputModel is empty
        if(val.length == undefined) return
        //remove label from model if other label is clicked = InputModel changes to other node
        if(val.length == 0) {
          this.model = []
          return
        }

        //otherwise add InputModel to model
        //clear model first (sometimes old labels are still in model, when users close labelMenu without pressing enter) 
        this.model = []
        for(let el of this.InputModel) {
          this.model.push(el)
        }
      },
    },

    methods: {
      edit (index, item) {
        if (!this.editing) {
          if(this.editingOldItem == null) {
            this.editingOldItem = Object.assign({}, item)
          }
          this.editing = item
          this.index = index
        } else {
          //insert server submit here : case new label exists already [merge handled by server], new label length is 0 [delete], else change
          if(item.text.length == 0) {
            this.$store.dispatch('deleteLabelandRefresh', [this.editingOldItem.text, item.text])
          }
          else {
            //make changes if necessary
            if(this.editingOldItem.text != item.text) {
              this.$store.dispatch('updateLabelandRefresh', [this.editingOldItem.text, item.text])
            }
          }
          //should handle promise reject somehow
          this.editing = null
          this.index = -1
          this.editingOldItem = null
        }
      },

      filter (item, queryText, itemText) {
        if (item.header) return false

        const hasValue = val => val != null ? val : ''

        const text = hasValue(itemText)
        const query = hasValue(queryText)

        //when filter does not return an item, reset the currently selected item in the list
        if(!(text.toString().toLowerCase().indexOf(query.toString().toLowerCase()) > -1)) {
          this.listIndex = -1
        }

        return text.toString()
          .toLowerCase()
          .indexOf(query.toString().toLowerCase()) > -1
      },

      //process native change event of v-combobox
      forwardChange (array) {
        //act only if edit mode is not active
        if(this.editing == null) {
          //action if user deleted all labels = delete this annotation
          let returnArray = []
          if(array.length == 0) {
            returnArray = ["delete", null]
          }

          else {
            returnArray = array
          }

          //prevent next input so label is not created unintentionally
          this.preventNextInput = true

          //emit event to trigger label change
          this.$emit("newLabel", returnArray)
          //should also trigger proper edit
          // >> TBD
        }
      },

      //method needed to prevent two lables from being created when users search for a label
      listIndexChanged (array) {
        //prevent change of listIndex to -1 when a label is selected from the list with 'enter'
        if(this.listIndex != -1 && array == -1) {
          if(this.preventNextInput == true) {
            //if this error was prevented once > reset the boolean
            this.preventNextInput = false
          }
        }
        else {
          this.listIndex = array
        }
      },

      closeInput () {
        this.$emit("closeEvent")
      },
    },
  }
</script>

<style>

b {
  color: black;
}

</style>}
