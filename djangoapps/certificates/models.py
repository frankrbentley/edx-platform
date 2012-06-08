import settings

from django.contrib.auth.models import User
from django.db import models


'''
Certificates are created for a student and an offering of a course.

When a certificate is generated, a unique ID is generated so that 
the certificate can be verified later. The ID is a UUID4, so that
it can't be easily guessed and so that it is unique. Even though
we save these generated certificates (for later verification), we
also record the UUID so that if we regenerate the certificate it
will have the same UUID.

If certificates are being generated on the fly, a GeneratedCertificate
should be created with the user, certificate_id, and enabled set 
when a student requests a certificate. When the certificate has been
generated, the download_url should be set.

Certificates can also be pre-generated. In this case, the user,
certificate_id, and download_url are all set before the user does
anything. When the user requests the certificate, only enabled
needs to be set to true.

'''

class GeneratedCertificate(models.Model):
    user = models.ForeignKey(User, db_index=True)
    certificate_id = models.CharField(max_length=32)
    graded_certificate_id = models.CharField(max_length=32, null=True)
    
    download_url = models.CharField(max_length=128, null=True)
    graded_download_url = models.CharField(max_length=128, null=True)
    
    grade = models.CharField(max_length=5, null=True)
    
    # enabled should only be true if the student has earned a grade in the course
    # The student must have a grade and request a certificate for enabled to be True
    enabled = models.BooleanField(default=False)


def certificate_state_for_student(student, grade):
    '''
    This returns a dictionary with a key for state, and other information. The state is one of the
    following:
    
    unavailable - A student is not elligible for a certificate.
    requestable - A student is elligible to request a certificate
    generating - A student has requested a certificate, but it is not generated yet.
    downloadable - The certificate has been requested and is available for download.
    
    If the state is "downloadable", the dictionary also contains "download_url" and "graded_download_url".
    
    '''
    
    if grade:
        #TODO: Remove the following after debugging
        if settings.DEBUG_SURVEY:
            return {'state' : 'requestable' }
        
        try:
            generated_certificate = GeneratedCertificate.objects.get(user = student)
            if generated_certificate.enabled:
                if generated_certificate.download_url:
                    return {'state' : 'downloadable',
                             'download_url' : generated_certificate.download_url,
                             'graded_download_url' : generated_certificate.graded_download_url}
                else:
                    return {'state' : 'generating'}
            else:
                # If enabled=False, it may have been pre-generated but not yet requested
                # Our output will be the same as if the GeneratedCertificate did not exist
                pass
        except GeneratedCertificate.DoesNotExist:
            pass
        return {'state' : 'requestable'}
    else:
        # No grade, no certificate. No exceptions
        return {'state' : 'unavailable'}
