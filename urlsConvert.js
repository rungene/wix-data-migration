const { media } = require('@wix/sdk');
async function convertUrls(internalUrls) {
  try {
    const urls = internalUrls.split(',').map((url) => url.trim());
    const absoluteUrls = await Promise.all(urls.map((convertUrl) => {
      const { url } = media.getImageUrl(convertUrl);

      return url
    }
  ));
    console.log(absoluteUrls.join(','));
  } catch (error) {
    console.error('Error onverting URLS:', error);
    process.exit(1);
  }
}

process.stdin.on('data', async (data) => {
  const internalUrls = data.toString().trim();
  await convertUrls(internalUrls);
});
