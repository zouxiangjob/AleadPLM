from rest_framework import serializers

from lead.apps.production.models import Files, Mpart


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = ['name', 'attachment']
        read_only_fields = ['id']
        extra_kwargs = {
            'attachment': {'write_only': True}
        }


class MpartsSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True,required=False,read_only=True)

    class Meta:
        model = Mpart
        fields = '__all__'
        read_only_fields = ['id']

    def create(self, validated_data):
        print("validated_data:", validated_data)
        files_data = validated_data.pop('files', [])
        mpart = Mpart.objects.create(**validated_data)

        if files_data:
            for f in files_data:
                Files.objects.create(mpart=mpart, **f)
        return mpart