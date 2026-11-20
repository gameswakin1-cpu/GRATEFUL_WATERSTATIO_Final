from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.urls import reverse


class VercelPrivateBlobStorage(Storage):
    def _blob(self):
        try:
            from vercel.blob import sync as blob
        except ImportError as exc:
            raise ImproperlyConfigured(
                'Install vercel-blob to use Vercel Blob for private media.'
            ) from exc
        return blob

    def _open(self, name, mode='rb'):
        if mode not in ('rb', 'r'):
            raise ValueError('Vercel Blob files can only be opened for reading.')
        result = self._blob().get_blob(name, access='private')
        return ContentFile(result.body, name=name)

    def _save(self, name, content):
        result = self._blob().put_blob(
            name,
            content.chunks(),
            access='private',
            content_length=content.size,
            content_type=getattr(content, 'content_type', None),
            add_random_suffix=True,
        )
        return result.pathname

    def delete(self, name):
        self._blob().delete_blob(name)

    def exists(self, name):
        try:
            self._blob().head_blob(name)
        except FileNotFoundError:
            return False
        return True

    def size(self, name):
        return self._blob().head_blob(name).size

    def url(self, name):
        return reverse('private_media', kwargs={'path': name})


def vercel_payment_proof_storage():
    return VercelPrivateBlobStorage()


def vercel_private_blob_storage():
    return VercelPrivateBlobStorage()
