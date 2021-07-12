<template>
  <v-navigation-drawer
    class="nav"
    fixed
    clipped
    right
    permanent
    :expand-on-hover="expandOnHover"
  >
    <v-list-item class="px-2">
      <v-list-item-content>
        <p class="title font-weight-thin text-left">CODEBOOK</p>
      </v-list-item-content>
      <v-list-item-icon>
        <v-icon @click="expandOnHover = !expandOnHover">
          <template v-if="expandOnHover">mdi-lock</template>
          <template v-else>mdi-lock-open</template>
        </v-icon>
      </v-list-item-icon>
    </v-list-item>

    <draggable 
      v-model="items"
      tag="v-list"
    >
      
        <v-list-item
          v-for="(item, i) in items"
          :key="i"
        >
            <v-chip
              :color="`${item.color}`"
              label
              small
            >
              <span class="pr-2">
                {{ item.text }}
              </span>
            </v-chip>

        </v-list-item>
    </draggable>

  </v-navigation-drawer>
</template>

<script>
  import draggable from 'vuedraggable'

  export default {
    name: 'CodebookDrawer',

    components: {
      draggable,
    },

    data: () => ({
      expandOnHover: true,
    }),

    computed: {
      items: {
        get() {
          return this.$store.state.codes
        },
        set(value) {
          this.$store.dispatch('updateList', value)
        }
      },

      dragOptions() {
        return {
          animation: 200,
          group: "description",
          disabled: false,
          ghostClass: "ghost"
        }
      },
    },

    methods: {
      
    },
  };
</script>

<style>
  .flip-list-move {
    transition: transform 1s;
  }

  .px-2 p {
    padding-left: 8px;
  } 

  .nav {
    padding-top: 50px;
  }

</style>
