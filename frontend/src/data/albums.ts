export interface AlbumImage {
	src: string;
	alt: string;
}

export interface Album {
	slug: string;
	title: string;
	tags: string[];
	published: string;
	cover: string;
	hover: string;
	images: AlbumImage[];
}

const photoFiles = [
	'photo-01.webp',
	'photo-02.webp',
	'photo-03.webp',
	'photo-04.webp',
	'photo-05.webp',
	'photo-06.webp',
	'photo-07.webp',
	'photo-08.webp',
] as const;

interface AlbumSeed {
	slug: string;
	title: string;
	tags: string[];
	published: string;
}

const albumSeeds: AlbumSeed[] = [
	{
		slug: 'small-cat-big-dreams',
		title: 'Small Cat - Big Dreams',
		tags: ['ZZZ', 'Ju Fufu'],
		published: '2026-01-01',
	},
	{
		slug: 'dorothys-dorodream',
		title: 'Dorothy’s Dorodream',
		tags: ['Nikke: Goddess of Victory'],
		published: '2026-01-01',
	},
	{
		slug: 'kivotosi-heat',
		title: 'Kivotosi Heat',
		tags: ['Blue Archive', 'Kisaki'],
		published: '2026-01-01',
	},
	{
		slug: 'a-detour-to-remember',
		title: 'A Detour to Remember',
		tags: ['Forgotten Island'],
		published: '2026-01-01',
	},
	{
		slug: 'heartsteel-splash-out',
		title: 'HeartSteel Splash-Out!',
		tags: ['League of Legends', 'Sett'],
		published: '2026-01-01',
	},
	{
		slug: 'ripples-rejoined',
		title: 'Ripples Rejoined',
		tags: ['Honkai: Star Rail', 'Cyrene'],
		published: '2026-01-01',
	},
	{
		slug: 'vestiges-of-the-old-order',
		title: 'Vestiges of the Old Order',
		tags: ['Sakamoto Days', 'Osaragi'],
		published: '2026-01-01',
	},
	{
		slug: 'a-doll-among-many',
		title: 'A Doll Among Many',
		tags: ['Honkai: Star Rail', 'Herta'],
		published: '2026-01-01',
	},
];

function buildImages(title: string, start: number): AlbumImage[] {
	return photoFiles.map((_, index) => {
		const file = photoFiles[(start + index) % photoFiles.length];
		return {
			src: `/images/${file}`,
			alt: `${title} — photograph ${index + 1}`,
		};
	});
}

export const albums: Album[] = albumSeeds.map((album, index) => {
	const images = buildImages(album.title, index);

	return {
		...album,
		cover: images[0].src,
		hover: images[1].src,
		images,
	};
});

export function getAlbumBySlug(slug: string): Album | undefined {
	return albums.find((album) => album.slug === slug);
}
