<template>
  <!-- No document loaded yet-->
  <div v-if="this.$store.state.currentDocument == null">
    <UserWelcomeComponent />
  </div>

  <v-container v-else>
    <v-row justify="center" class="mb-6 mt-8">
      <v-col cols="10">
        <h1 class="font-weight-light text-center">Analytics quick peek 🔍</h1>
        <h3 class="font-weight-light">The following information are supposed to provide a quick glance of your data without the need to download your dataset and use additional software.</h3>
      </v-col>
    </v-row>

    <v-row>
      <v-col md="6">
        <v-card>
          <v-card-title>{{currentDocument.name}}</v-card-title>
          <v-card-subtitle>{{ dateTranslate(currentDocument.lastChange) }}</v-card-subtitle>
          <v-card-text>
            <h3>Settings</h3>
            <p>Type: {{ inputTypeTranslate(currentDocument.inputType) }}</p>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col>
        <v-card>
          <v-card-text>% coded of total</v-card-text>
          <v-card-text> <b> {{ this.$store.state.codes.length }} </b> Codes used overall </v-card-text>
          <v-card-text> <b> {{ this.$store.state.annotations.length }} </b> Annotations made overall </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Codes overview data table -->
    <v-row justify="center" class="mt-8"> 
      <v-col>
        <v-card>
          <v-card-title>Label statistics
            <v-spacer></v-spacer>
            <v-text-field
              v-model="search"
              append-icon="mdi-magnify"
              label="Search"
              single-line
              hide-details
            ></v-text-field>
          </v-card-title>
          <v-data-table
            :headers="headers"
            :items="annotationsSummary"
            item-key="name"
            :search="search"
            :single-expand="singleExpand"
            :expanded.sync="expanded"
            show-expand
          >
            <template v-slot:item.name="{ item }">
              <v-chip
                :color="labelColor(item.name)"
                label
                small
              >
                <span class="pr-2">
                  {{ item.name }}
                </span>
              </v-chip>
            </template>

            <template v-slot:expanded-item="{ headers, item }">
              <td :colspan="headers.length"> {{ item.example == '' ? 'Looks like you have not used this label yet.' : item.example }} </td>
            </template>

          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

  </v-container>

</template>

<script>
import UserWelcomeComponent from '../components/UserWelcomeComponent'

export default {
  name: 'Analytics',

  components: {
    UserWelcomeComponent,
  },

  data: () => ({
    //search data table
    search: '',
    //header for data table
    headers: [
      { text: '', value: 'data-table-expand' },
      {
        text: 'Label',
        align: 'start',
        value: 'name',
      },
      { text: 'Count', value: 'count'},
    ],

    //placeholders for expanded table
    expanded: [],
    singleExpand: false,

  }),

  computed: {
    currentDocument() {
      return this.$store.state.currentDocument
    },

    annotationsSummary() {
      let summaryObject = []
      for(let code of this.$store.state.codes) {
        const label = code.text
        summaryObject.push({
          name: label,
          count: 0,
          example: '',
        })
      }

      for(let an of this.$store.state.annotations) {
        const index = summaryObject.findIndex( label => label.name == an.label )
        //prevent cases where label cannot be found = when label is default, then do not display in analysis page for now
        if(index != -1) {
          summaryObject[index].count = summaryObject[index].count + 1
          //populate example with first occurance
          summaryObject[index].example == '' ? summaryObject[index].example = an.id : null
        }
      }

      return summaryObject
    }
  },

  methods: {
    inputTypeTranslate(inputType) {
      if(inputType == 0) {
        return "Text"
      }
      else if(inputType == 1) {
        return "Laddering"
      }
      else if(inputType == 2) {
        return "LadderBot"
      }
    },

    dateTranslate(timestamp) {
      const date = new Date(timestamp * 1000)
      return date.toLocaleString()
    },

    labelColor(labelName) {
      try {
        let element = this.$store.state.codes.find( code => code.text == labelName )
        return element.color
      }
      catch {
        return null
      }
    },
  }
};
</script>
