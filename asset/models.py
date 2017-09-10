# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse

class Asset(models.Model):
    label       = models.CharField('產標編號', help_text='Ex: xxxxxxxxxx-yyyyy',
                                   unique=True, max_length=100)
    name        = models.CharField('物品類別', help_text='Ex: 行動電話機',
                                   max_length=100)
    date        = models.DateField('產標日期')
    years       = models.SmallIntegerField('年限')
    custodian   = models.CharField('保管人', help_text='Ex: 徐慰中',
                                   max_length=50)
    description = models.CharField('描述', help_text='Ex: iPhone 6 plus',
                                   max_length=100)
    remark      = models.TextField('備註', help_text='Ex: 密碼是xxxx',
                                   blank=True)

    class Meta:
        verbose_name = '財產'
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return '%s: %s (%s)' % (self.label, self.name, self.description)

    def get_absolute_url(self):
        return reverse('asset:detail', kwargs={
            'slug': self.label,
        })

    @property
    def latest_log(self):
        return self.transferlog_set.latest()


class TransferLog(models.Model):
    BUY      = 'BUY'
    TRANSFER = 'TRANSFER'
    RETURN   = 'RETURN'
    SCRAP    = 'SCRAP'
    STATUS_CHOICES = (
        (BUY, '購入'),
        (TRANSFER, '轉移/取用'),
        (RETURN, '歸還'),
        (SCRAP, '報廢'),
    )

    status   = models.CharField(choices=STATUS_CHOICES, max_length=20)
    time     = models.DateTimeField(auto_now_add=True)
    asset    = models.ForeignKey(Asset, on_delete=models.CASCADE)
    new_user = models.ForeignKey('website.Member', null=True, blank=True, on_delete=models.SET_NULL)
    location = models.CharField(blank=True, max_length=255, help_text='Ex: 座位')
    remark   = models.CharField(blank=True, max_length=255, help_text='物品狀態(壞了?)、用途說明')

    class Meta:
        unique_together = ('asset', 'time')
        ordering = ['-time']
        get_latest_by = 'time'

    def __unicode__(self):
        return unicode(self.asset) + self.get_status_display()

    def clean(self):
        super(TransferLog, self).clean()

        if self.asset.transferlog_set.filter(status=self.SCRAP).exclude(pk=self.pk).exists():
            raise ValidationError('This asset is already scrapped.')
        if self.status == self.BUY and self.pk is None:
            raise ValidationError('The status "BUY" shall only be created automatically.')
        if self.status == self.TRANSFER and self.new_user is None:
            raise ValidationError('Missing the transfer target (the new user).')
        if self.status in (self.RETURN, self.SCRAP) and self.new_user is not None:
            raise ValidationError("There shouldn't be new user for a returned/scrapped asset.")
