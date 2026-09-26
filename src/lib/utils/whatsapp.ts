export type Provider = 'Telkomsel' | 'Indosat' | 'XL' | 'AXIS' | 'Tri' | 'Smartfren' | 'Unknown';

export function getWhatsAppProvider(number: string): Provider {
    if (!number) return 'Unknown';

    // Normalize number: hapus spasi, strip, dll
    let cleanNumber = number.replace(/\D/g, '');

    // Ubah 628 menjadi 08
    if (cleanNumber.startsWith('628')) {
        cleanNumber = '08' + cleanNumber.substring(3);
    } else if (cleanNumber.startsWith('+628')) {
        cleanNumber = '08' + cleanNumber.substring(4);
    }

    if (!cleanNumber.startsWith('08') || cleanNumber.length < 4) {
        return 'Unknown';
    }

    const prefix = cleanNumber.substring(0, 4);

    // Telkomsel: 0811, 0812, 0813, 0821, 0822, 0823, 0851, 0852, 0853
    if (['0811', '0812', '0813', '0821', '0822', '0823', '0851', '0852', '0853'].includes(prefix)) {
        return 'Telkomsel';
    }

    // Indosat Ooredoo: 0814, 0815, 0816, 0855, 0856, 0857, 0858
    if (['0814', '0815', '0816', '0855', '0856', '0857', '0858'].includes(prefix)) {
        return 'Indosat';
    }

    // XL: 0817, 0818, 0819, 0859, 0877, 0878
    if (['0817', '0818', '0819', '0859', '0877', '0878'].includes(prefix)) {
        return 'XL';
    }

    // AXIS: 0831, 0832, 0833, 0838
    if (['0831', '0832', '0833', '0838'].includes(prefix)) {
        return 'AXIS';
    }

    // Tri (3): 0895, 0896, 0897, 0898, 0899
    if (['0895', '0896', '0897', '0898', '0899'].includes(prefix)) {
        return 'Tri';
    }

    // Smartfren: 0881, 0882, 0883, 0884, 0885, 0886, 0887, 0888, 0889
    if (['0881', '0882', '0883', '0884', '0885', '0886', '0887', '0888', '0889'].includes(prefix)) {
        return 'Smartfren';
    }

    return 'Unknown';
}

export function getProviderColor(provider: Provider): string {
    switch (provider) {
        case 'Telkomsel': return 'bg-red-600 text-white';
        case 'Indosat': return 'bg-yellow-400 text-black';
        case 'XL': return 'bg-blue-600 text-white';
        case 'AXIS': return 'bg-purple-600 text-white';
        case 'Tri': return 'bg-black text-white';
        case 'Smartfren': return 'bg-pink-600 text-white';
        default: return 'bg-gray-300 text-gray-800';
    }
}
