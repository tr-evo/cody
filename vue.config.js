module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  devServer: {
    open: process.platform === 'darwin',
    host: '127.0.0.1',
    https: false,
    hotOnly: false,
  },
}