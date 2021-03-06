CREATE DATABASE repology;
CREATE USER repology WITH PASSWORD 'repology';
GRANT ALL PRIVILEGES ON DATABASE repology_test TO repology_test;

\c repology repology

CREATE TABLE links (
    url text NOT NULL PRIMARY KEY,
    next_check timestamp with time zone NOT NULL DEFAULT now(),
    last_checked timestamp with time zone,

	ipv4_last_success timestamp with time zone,
	ipv4_last_failure timestamp with time zone,
	ipv4_success boolean,
	ipv4_status_code smallint,
	ipv4_permanent_redirect_target text,

	ipv6_last_success timestamp with time zone,
	ipv6_last_failure timestamp with time zone,
	ipv6_success boolean,
	ipv6_status_code smallint,
	ipv6_permanent_redirect_target text
);

INSERT INTO links(url) VALUES
	('https://repology.org/'),             -- good
	('http://repology.org/'),              -- good + permanent redirect
	('badschema://repology.org/'),         -- bad schema
	('ftp://nonexistent.repology.org/'),   -- ftp
	('ftp://repology.org/nonexistent'),    -- ftp
	('https://nonexistent.repology.org/'), -- nonexistent hostname
	('https://repology.org:444/'),         -- cannot connect
	('https://repology.org/nonexistent'),  -- nonexistent path (404)
	('https://./'),                        -- bad url
	('https://mepis.org/foo');             -- blacklisted url

CREATE TABLE statistics (
	num_urls_checked integer NOT NULL DEFAULT 0
);

INSERT INTO statistics VALUES(DEFAULT);
