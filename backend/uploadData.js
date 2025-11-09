import { mediaManager } from 'wix-media-backend';

export async function uploadData(fileName, fileContent) {
  try {
    const buffer = Buffer.from(fileContent, 'utf-8');
    const uploadResult = await mediaManager.upload(
      '/data',
      buffer,
      fileName,
      { mediaOptions: { mimeType: 'application/json' } }
    );
    return { success: true, fileUrl: uploadResult.fileUrl };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

