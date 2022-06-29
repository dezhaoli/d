from uuid import uuid4
import io
import os

class FormFile(object):
    def __init__(self, fileobj, formname=None, filename=None, boundary=None):
        #: Boundary value either passed in by the user or created
        self.boundary_value = boundary or uuid4().hex
        self.boundary = '--' + self.boundary_value
        
        self._fileobj = fileobj
        self._buffer = io.BytesIO()
        
        # write boundary and header
        self._remain_len = 0
        self._remain_len += self._buffer.write(self.boundary + '\r\n')
        header = 'Content-Disposition: form-data'
        if formname: header += '; name="%s"' % formname
        if filename: header += '; filename="%s"\r\n' % filename
        self._remain_len += self._buffer.write(header)
        self._remain_len += self._buffer.write(
            'Content-Type: application/octet-stream\r\n')
        self._remain_len += self._buffer.write('\r\n')

        current_offset = self._fileobj.tell()
        self._fileobj.seek(0, 2)
        self._file_size = self._fileobj.tell() - current_offset
        self._fileobj.seek(current_offset, 0)

        self._end_loaded = False
        self._start_len = self._remain_len
        self._len = None

    @property
    def len(self):
        """Length of the multipart/form-data body.
        requests will first attempt to get the length of the body by calling
        ``len(body)`` and then by checking for the ``len`` attribute.
        """
        # If _len isn't already calculated, calculate, return, and set it
        return self._len or self._calculate_length()

    def _calculate_length(self):
        """
        This uses the parts to calculate the length of the body.
        This returns the calculated length so __len__ can be lazy.
        """
        boundary_len = len(self.boundary)
        end_len = boundary_len + 6
        self._len = self._start_len + self._file_size + end_len
        return self._len

    @property
    def content_type(self):
        return str('multipart/form-data; boundary=%s' % self.boundary_value)

    def read(self, size=-1):
        if size == -1:
            if not self._end_loaded:
                self._buffer.seek(0, 2)
                self._buffer.write(self._fileobj.read())
                self._buffer.write('\r\n' + self.boundary + '--\r\n')
            self._buffer.seek(0, 0)
            data = self._buffer.read()
            self._buffer.seek(0, 0)
            self._buffer.truncate()
            self._remain_len = 0
            self._end_loaded = True
            return data
        else:
            # httplib use 8192 as block size, it's too small
            if size <= 8192:
                size = size * 1024

            if not self._end_loaded and size > self._remain_len:
                self._buffer.seek(0, 2)
                self._remain_len += self._buffer.write(
                    self._fileobj.read(size - self._remain_len)
                )

                if size > self._remain_len:
                    self._remain_len += self._buffer.write('\r\n' + self.boundary + '--\r\n')
                    self._end_loaded = True

            self._buffer.seek(0, 0)
            data = self._buffer.read(size)
            self._remain_len -= len(data)
            remain = None
            if self._remain_len > 0:
                remain = self._buffer.read()
            self._buffer.seek(0, 0)
            self._buffer.truncate()
            if remain:
                self._buffer.write(remain)
            
            return data
