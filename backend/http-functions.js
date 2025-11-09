import { ok, serverError } from 'wix-http-functions';
import { uploadData } from 'backend/uploadData';

export async function post_uploadData(request) {
  try {
    const body = await request.body.json();
    const { fileName, fileContent } = body;
    const result = await uploadData(fileName, fileContent);
    return ok(result);
  } catch (err) {
    return serverError({ error: err.message });
  }
}

