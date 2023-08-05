module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  devServer: {
    open: process.platform === 'darwin',
    host: [
      'localhost',
      '127.0.0.1',
      'http://cody.myresearchprocess.com/',
    ],
    port: 62041, // CHANGE YOUR PORT HERE!
    https: false,
    hotOnly: false,
  },
}