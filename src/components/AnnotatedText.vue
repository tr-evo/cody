<template>
  <span>
    <span
      v-for="span in spans"
      :key="span.id"
      :data-span-id="span.id"
      :id="getSpanID(span)"
      :class="getSpanClasses(span)"
      :style="getSpanStyle(span)"
      v-bind="spanAttributes"
      @click="spanEvent"
    >{{ span.text }}</span>
  </span>
</template>

<script>
import c_c from 'color-mixer'
import { buildSpanList } from '../util/buildSpanList'

export default {
  name: 'AnnotatedText',
  props: {
    text: String,
    //to craft ID
    conversation: String,
    attribute: String,
    annotations: {
      type: Array,
      default: function() {
        return []
      },
    },
    getAnnotationColor: {
      type: Function,
      default: function() {
        return '#ffffff'
      },
    },
    getAnnotationInfo: Function,
    spanEvents: {
      type: Object,
      default: function() { return {} }
    },
    getSpanClasses: {
      type: Function,
      default: function() { return () => {} }
    },
    spanAttributes: {
      type: Object,
      default: function() { return {} }
    },
  },
  computed: {
    spans: function() {
      const spans = buildSpanList(this.text, this.annotations)
      return spans
    },
  },
  methods: {
    elementSpanId(el) {
      let spanId = el.attributes['data-span-id'].value
      spanId = Number(spanId)
      return spanId
    },
    spanById(spanId) {
      const spans = this.spans.filter(span => {
        return span.id === spanId
      })
      const span = spans[0]
      return span
    },
    getAnnotations(annotationIds) {
      const annotations = this.annotations.filter(annotation => {
        return annotationIds.includes(annotation.id)
      })
      return annotations
    },
    getSpanStyle: function(span) {
      return {
        backgroundColor: this.getSpanColor(span)
      }
    },
    getSpanColor: function(span) {
      let color = null
      const annotationIds = span.annotationIds
      const annotations = this.getAnnotations(annotationIds)
      let colors = annotations.map(annotation => this.getAnnotationColor(annotation))
      colors = [...new Set(colors)]
      if (colors.length > 1) {
        colors = colors.map(color => {
          return new c_c.Color({hex: color})
        })
        let mixedColor = colors[0]
        for(let x = 0; x < colors.length - 1; x++) {
          mixedColor = new c_c.Color({mix: [mixedColor, colors[x+1]]})
        }
        color = mixedColor.hex()
      } else {
        color = colors[0]
      }
      return color
    },

    //removed function to pass spanEvents from parent for custom function for click event
    spanEvent(e) {
      const spanId = this.elementSpanId(e.target)
      const span = this.spanById(spanId)
      const annotationIds = span.annotationIds
      const annotations = this.getAnnotations(annotationIds)

      //prevent event from firing when clicking on an span without label
      if(annotations.length != 0) {
        this.$emit("editLabelEvent", [e, annotations])
      }
    },

    //construct id for span: first char of conversation - first char of attribute - start - length
    getSpanID(span) {
      let thisAnnotation = this.$store.state.annotations.find(an => an.id == span.text)
      let returnString = ''
      if(thisAnnotation != undefined) {
        //for annotated Sections
        returnString = thisAnnotation.annotationID
      }
      else {
        //for normal Sections
        returnString = this.conversation.charAt(0) + '-' + this.attribute.charAt(0) + '-' + span.annotationID
      }
      return returnString
    },
  },
}
</script>