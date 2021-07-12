<template>
	<v-container>
		<v-row justify="center" class="mb-6 mt-8">
			<v-col cols="10">
				<h1 class="font-weight-light text-center">Load an existing document 📦</h1>
				<h3 class="font-weight-light text-center">Continue your work by selecting on of the documents below!</h3>
			</v-col>
		</v-row>

		<v-row v-if="serverStatus == 0" class="mt-12">
			<v-col>
				<v-card
					class="mx-auto"
					outlined
					max-width="400px"
				>
					<v-img
						class="align-end"
						height="200px"
						src="@/assets/404.jpg"
						gradient="to bottom, rgba(255,255,255,.0) 50%, rgba(237,237,237,1)"
					>
						<v-card-title class="display-1 font-weight-light">404 · Offline</v-card-title>
					</v-img>
					<v-card-subtitle>We are having trouble reaching the server</v-card-subtitle>
					<v-card-text class="subtitle-1 font-weight-light">Sorry! Please check you internet connection, and try again now or later.</v-card-text>
				</v-card>
			</v-col>
		</v-row>
	
		<v-row v-else justify="center">
			<!--No document created yet-->
			<v-col v-if="documents.length == 0" cols="5">
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

			<v-col
				v-for="doc in documents"
				:key="doc.id"
				:cols=12
				:sm=6
			>
				<v-hover
					v-slot:default="{ hover }"
				>
					<v-card
						@click="loadDocument(doc.id)"
						:dark="currentDocumentID == doc.id ? true : false"
						:elevation="hover ? 12 : 2"
					>
					<v-toolbar
						class="pt-2"
						dense
						flat>
						<v-toolbar-title class="font-weight-bold">{{doc.name}}</v-toolbar-title>
						<v-spacer></v-spacer>
						<v-btn icon
							@click.stop="deleteDocumentDialog(doc.id)">
							<v-icon>mdi-delete</v-icon>
						</v-btn>
					</v-toolbar>
						<v-card-subtitle>{{ dateTranslate(doc.lastChange) }}</v-card-subtitle>
						<v-card-text>
							<h3>Settings</h3>
							<p>Type: {{ inputTypeTranslate(doc.inputType) }}</p>
						</v-card-text>
					</v-card>
				</v-hover>
			</v-col>
		</v-row>

		<!-- Dialog to accept deletion of document -->
		<template>
			<v-row justify="center">
				<v-dialog v-model="dialog" persistent max-width="290">
					<v-card>
						<v-card-title class="headline">Delete document [{{ getDeletionDocumentName() }}]?</v-card-title>
						<v-card-text>You cannot undo the deletion of a document. Your labels and annotations will be removed. Are you sure you want to proceed?</v-card-text>
						<v-card-actions>
							<v-spacer></v-spacer>
							<v-btn color="red lighten-1" text @click="dialog = false">Take me back</v-btn>
							<v-btn color="green darken-1" text @click="deleteDocument">Continue</v-btn>
						</v-card-actions>
					</v-card>
				</v-dialog>
			</v-row>
		</template>
		
	</v-container>
</template>

<script>

export default {
	name: 'Documents',

	components: {

	},

	data: () => ({
		serverStatus: null,
		//open delete dialog
		dialog: false,
		toBeDeleted: null,
	}),

	created: function() {
		this.$store.dispatch('getDocuments')
		.then((res) => {
			//success
			this.serverStatus = res
		}, (res) => {
			//fail
			this.serverStatus = res
		})
	},

	computed: {
		documents() {
			return this.$store.state.serverDocuments
		},

		currentDocumentID() {
			try {
				return this.$store.state.currentDocument.id
			} 
			catch {
				return null
			}
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

		loadDocument(id) {
			this.$store.dispatch("changeToDocument", id)
			.then(() => {
				this.$router.push('/document')
			})
		},

		goto(element) {
			this.$router.push({ name: element})
		},

		deleteDocumentDialog(id) {
			this.dialog = true
			this.toBeDeleted = id
		},

		deleteDocument() {
			this.$store.dispatch("deleteDocument", this.toBeDeleted)
			.then(() => {
				this.toBeDeleted = null
				this.dialog = false
			})
		},

		getDeletionDocumentName() {
			let docName = this.documents.find(doc => doc.id == this.toBeDeleted)
			if(docName == undefined) {
				return "No Document found"
			}
			else {
				return docName.name
			}
		}
	}
};
</script>
