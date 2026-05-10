-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 10, 2026 at 05:42 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_siakad_blockchain`
--

-- --------------------------------------------------------

--
-- Table structure for table `diplomas`
--

CREATE TABLE `diplomas` (
  `id` char(36) NOT NULL,
  `studies_id` char(36) DEFAULT NULL,
  `graduationYear` varchar(4) DEFAULT NULL,
  `university_id` char(36) DEFAULT NULL,
  `student_id` char(36) DEFAULT NULL,
  `diploma_number` varchar(255) DEFAULT NULL,
  `ipfs_cid` text DEFAULT NULL,
  `document_hash` varchar(255) DEFAULT NULL,
  `encrypted_key` text DEFAULT NULL,
  `iv` varchar(255) DEFAULT NULL,
  `tx_hash` varchar(255) DEFAULT NULL,
  `block_number` bigint(20) DEFAULT NULL,
  `status` enum('valid','revoked','pending') DEFAULT NULL,
  `issued_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `diplomas`
--

INSERT INTO `diplomas` (`id`, `studies_id`, `graduationYear`, `university_id`, `student_id`, `diploma_number`, `ipfs_cid`, `document_hash`, `encrypted_key`, `iv`, `tx_hash`, `block_number`, `status`, `issued_at`) VALUES
('854ee578-7063-43d0-8e5d-859a265a1a3c', '1a37dcfe-7ce9-433b-b3c4-9cb6080c9c8f', '2026', '310d497b-32c9-41c2-8fa2-416f2f8bfb35', 'bbcc3d5a-a5ce-443c-b20b-7c3d6cbcf39a', 'DIP-NUM-2311082017', 'QmcX7rohpqS2XPMFhbg3XeMppefn2hgLS4HfiFMYgNd2G6', 'ab9dc9879061a37c64576e2befd2b789f836dc23b1f4e6cebb24e62cc87a4bbc', 'c09d53cbca4eb7fb958d8943c987a026b217eb9347b0d7010fe00c995842915b59d5fa0a1091259b322d47de31dbd4432f96dca9de8572a92f22afa6342343e1af2d5fb23a4e71037149d5e3d630fb86e5f6a9b58c452487091155b1410303c2c7f7729133069a04be39ef699b67608294f23804659d46c9a2dcc3c6f02704e30b7a8a99e37542fe150cc6cad4284c33801fdad21e45588917a39323848d0e0a5116fea2aae1b96466297ca06e66f275f9ec87ab8454f99a26bc3df591adec3db292311aff1a05717ade39523f20f23deb9caff50275ea7dbfd8a7ab0414524f312e023fbaa8d4837a96ed9bb4e85a5ad75b145cc64be4c3aedd39819d31e4e6', 'a54a4d0e8b0c4e98506cb915fbda5f75', '9785fc531e2d3e27fb0f7ab230ca4ddaf055b77627ffa03697763cbf7b803444', 32, 'valid', '2026-05-10 08:38:54'),
('ecca4f20-59b4-4f45-834e-07fd1b010bff', '8c8f1440-d7ad-4197-b1b7-460f69d4c961', '2026', '310d497b-32c9-41c2-8fa2-416f2f8bfb35', 'bbcc3d5a-a5ce-443c-b20b-7c3d6cbcf39a', 'DIP-NUM-2311082018', 'QmYkUjj6m87S7miRRM8rP8sdvRxss7Cy7NWuE4RHHv1c2m', 'ab9dc9879061a37c64576e2befd2b789f836dc23b1f4e6cebb24e62cc87a4bbc', 'aedacbbd560c4befdf8cbb22e7ae952d5894045568b2be2481031ec9b6d1e48dc23cb0168c2804ddf340e28a18a0066b24d5e082dac4825116fc153d09a25208fb64041bd4d7c203f1538cc61b4bcaebd79eac6c9a1d45a92a028f65509f41994c5de042bae4e2724a90e771ad588705ccc887fc291f50f8961d32ea4a61d898f32ca137f7f4d9941757417f05738b4bb1728bb837ba29b386e0dcc3a6458a122540391832a08525b8f66e3a14f7b77aa6ca9218fcc30feca2913d518ec98b6fe1e6a44b005123a39495d603babd0cb44ea79db17b8aa880026b9374e691ae982484ac5b15ef2df1077e9326ed5d90c06651389a7c7ed1ab7cd1ee4dc2294efa', '41e1bcec179f2826ccfb0463fe04050a', NULL, NULL, 'pending', '2026-05-10 08:34:05');

-- --------------------------------------------------------

--
-- Table structure for table `students`
--

CREATE TABLE `students` (
  `id` char(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `public_key` text DEFAULT NULL,
  `rsa_private_key_encrypted` text DEFAULT NULL,
  `ktp_number` varchar(20) DEFAULT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `is_phone_verified` tinyint(1) DEFAULT NULL,
  `place_and_date_of_birth` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `password_hash` text DEFAULT NULL,
  `otp_secret` varchar(10) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `students`
--

INSERT INTO `students` (`id`, `name`, `public_key`, `rsa_private_key_encrypted`, `ktp_number`, `phone_number`, `is_phone_verified`, `place_and_date_of_birth`, `email`, `password_hash`, `otp_secret`, `created_at`) VALUES
('bbcc3d5a-a5ce-443c-b20b-7c3d6cbcf39a', 'Fitrah Septiandwi Sensi', '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA9MwFvKIlEflj+zZjI9wa\n0MgBFH/a4yNx5HVQ1+tkaHOB7sbyWujJqLGVptGOQvWm++NBe8RhnFYwIBDDK9KK\niddvYwPv4hzKSAmdgBhNxDr26CXylYLiOheCvC9QLhye94S+62tdGYFvwWZtW4uY\n8jD6FXNwJAF1mZ317B1xSsris9zBy82MO9rXd17hUmKQeCQcTwjLfb+8XJSwR3pR\nY1WGNMPWQd6b3snT4hGomX20s2ABJp+xCeJLzqmfazK8SIm21wd2o0GLR8Djcs/L\nyMsqCa02rVjFC6ol1BGnTZ8c/SQCMCZlkrIiQEUnIA/NOnfYW2M4SVZFeaWbJW4G\nJwIDAQAB\n-----END PUBLIC KEY-----\n', 'gAAAAABqAKPdFA0FHMkWz__pwNx4LQsJE31dOC-YkMm1Ne-TrCrNtgNvLtsJM9ymOes90IZiAOmjiE_ONW5KPr5tScc8wL2HTmEqsf2WfAfZDlZlhJ_v9E0enqsp9CnxZhfIvl1wxGUNZFRXLpeZ38K5-4cs9AU7zazO-cNup7NlezXsdy2oBpxjcFFvev34_Eiu25yV1XLgtsIn11t5_Q3R6z4kN2_E8GyMDV1nkllXBRY9Zg0AO8IR5zU6qWDGk83E4nEZtraPFYcC8kxNwIw3TFYTaxYwY0A8T3lq-qAWkIL1RTr5YL3Ze0Y56IcSRw7aVcxgt_k_I_2ojlMymbF0k_NDscuuzQuJpVhujEO9SdX_JuVtKZ3pMfTCjImZt3_zrSP3ItDOfYZnxL-9ClXENSYz6Bed8b8jvf9RyxMPr6v3yiHiuZDUPukCYOZFMbloRd98-Qa_54UakNL7A0xkoAa17gVu_u5n8oDeb8nXyw7n86NrMGUPe2_8LnR5k4YGIS4Eavy5wACxAZWjFd2QbGXkkNt41k4qN8A0WtCYUMyuX87Z1zFgZK7Fk0dgPlNnbGFtJwUyjPOQxkv8M98WAMNNKVWL7h44JEVkGwBBV8hKd9gO1prYw-fgTHkrcpSOxWpqb8l3g4fDodaUrzpvLNU_wD4J_vwjJAiFJO2nFdudKnKNK2PrChazG-GHuS37MWnk2AFs3jN1_vYkctIY348VmL8HeCMf7idq4w1MimgdOrHYZbJoKBXVjNYeEkwDOc-u2JORH-a6xPGN8TCR-depHp7u27RHPXUScQdRezfc3oE9NEz2ON49CO_IfuVtlAKqMqX64gAuC2t0i7ASuEug0_Ag5Jcdakcis-WGudHqDqaTZhoZBTuhAeILCQyp5joXxl8lmD4MkWVn-Upoeunx-db5D7hdvAJ8bi5VW9mn_OkgEPkDDqCWRYZaJVx_JD6EV1T8P7H8x24639xO0E-_Apxuy5q8zaoougyX-Hqa2UhEJjjB5ppGdAfJUEg0j22EmL78SCuPOu9P3ACtHhQNvV9Jk5KhBe-ogn0cGc55tJyujP3NHKgdG0nEpWy8rTNJxhIau2OiPP95yPBS-PvU38pGMHz-sx1oqygJLtErbENiAuFMZeyBOuxHVkfK2TyKX20n_EVKy99sLTTIjky9B8ZnPWD0fmRv-cD2txkTTwbttUDvQZxz9ZUEHxXFnMeZrSjMQWot8rO6hS5qW0J2aM_iBfRgKjp82srAQQsRYhQ9e32CIo7YnqA1vNPdoH9BnsPUfXoPcO9Mwyr_g4UwSpenew_d--xmZsjCTre-i2DK2Rf7i8tUV1K6f0VeDhK9sOHE4SaC08jNS_9j6vxZfOG9kXDPCa2FEHfDItuFimkHExsv9uR-n1zL1A13Bge0rFqP5Ws5wcCELOavzPuTCBAYDbaRfWqHq0rWDduOCBONK6i6WR8-qKFKcYRGF6lcxs9eIBitLDhF0KdxfbnksNWrfSrt5pASXb07zriHmP9RjD3YUSSnYfVMfZSvyVBffrGc6FoVV9LIQn-tXc5HmeF9yVHGvrHgWWLU9h6rpGTo9XK6PVNyTWX2-E6ijK9VGMWRQ3oP1ji_m3ik57rbK_l3BbD9RGAPt2x2ktMBXzCbPczw8VhyO36sd9rOVhiWE839EBKvJ_PHEkw5wsir_Wz-9BBcigBQMXi13Mpx6mWHuLTXzgdG6TJr6E7PRXwSCTkgokOgmidMqaOz0bCWzD8gGenx0asxIItetK8ktR2jocprs6vT3dKFW4JjpasO_78U0XNROCLp7EiW3aX4zWK2l2RxpAwMlOkDCTOqlQ_b098ehClGZhBXeN-vOAPTs3mi7x9aUU55Sdjm9DlmArlP9HuRjygOz732OGY71Mnx8cgOQCXqcR999_B0QDuBhD1kjJIDL1DF-PjATKbwWoBJybcn6M1bh9v7nfNC_17m3O9g24I-7mEdhZurH1VEJzPuRcmMAQDJ0J32DQQ6PwrMA7CBIdz9uMhMbrmWUhjQprjDidI0iRAZbnW4U6kwi6GPU6ald7e0zO3_Q4EIM-t36c8MP-cZjr6umZ7C6nbjY4PCuH6I0wlCN9ko4iR0MrFZrRlgv7ECbrpQBsAlz1SZnlgwRoFT8NkR3NUa8Hyxw3ODX0ecsr-LyAAwt2Nlt4fyYKt2raUkuqivl68NmgUaZuLG1nTkRi89ud7n7TCDfQcEySNuQ4r0NCXVnOOsBB5ofrrpnkWptORROGCD5jJfVFpKorV4vMSxA_u0bZE7gIy_iY-9rabocnwbRUQPRpML-lQqVVZ1ZeEm2Vc84iTH_FpcZBSZaqSDhplwC6PAam0=', '1302100909050002', '089530056181', 1, 'Solok, 2005-01-09', 'fitrah@gmail.com', '$argon2id$v=19$m=65536,t=3,p=4$1hpjbG3tfc+Z8/5fS0np3Q$n0/dodrnZLoj6hD+z+UwPo16U2FIE3vsvcf/xFiB6sg', NULL, '2026-05-10 08:27:25');

-- --------------------------------------------------------

--
-- Table structure for table `studies`
--

CREATE TABLE `studies` (
  `id` char(36) NOT NULL,
  `student_id` char(36) DEFAULT NULL,
  `university_id` char(36) DEFAULT NULL,
  `major` varchar(255) DEFAULT NULL,
  `level` varchar(50) DEFAULT NULL,
  `nim` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `studies`
--

INSERT INTO `studies` (`id`, `student_id`, `university_id`, `major`, `level`, `nim`) VALUES
('1a37dcfe-7ce9-433b-b3c4-9cb6080c9c8f', 'bbcc3d5a-a5ce-443c-b20b-7c3d6cbcf39a', '310d497b-32c9-41c2-8fa2-416f2f8bfb35', 'Teknologi Rekayasa Perangkat Lunak', 'D4', '2311082017'),
('37887b73-6270-4bec-83a8-31f0292ec00b', 'bbcc3d5a-a5ce-443c-b20b-7c3d6cbcf39a', '310d497b-32c9-41c2-8fa2-416f2f8bfb35', 'Teknik Informatika', 'S3', '2311082019'),
('8c8f1440-d7ad-4197-b1b7-460f69d4c961', 'bbcc3d5a-a5ce-443c-b20b-7c3d6cbcf39a', '310d497b-32c9-41c2-8fa2-416f2f8bfb35', 'Sistem Informasi', 'S2', '2311082018');

-- --------------------------------------------------------

--
-- Table structure for table `transactions`
--

CREATE TABLE `transactions` (
  `id` char(36) NOT NULL,
  `reference_id` char(36) DEFAULT NULL,
  `tx_hash` varchar(255) DEFAULT NULL,
  `tx_type` enum('REGISTER_UNIVERSITY','ISSUE_DIPLOMA','VERIFY_DIPLOMA','REVOKE_DIPLOMA','UPDATE_ACCREDITATION') DEFAULT NULL,
  `status` enum('pending','success','failed') DEFAULT NULL,
  `block_number` bigint(20) DEFAULT NULL,
  `gas_used` bigint(20) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `transactions`
--

INSERT INTO `transactions` (`id`, `reference_id`, `tx_hash`, `tx_type`, `status`, `block_number`, `gas_used`, `created_at`) VALUES
('5f867f32-2fe3-4b5c-b487-e30388e6dfd5', '854ee578-7063-43d0-8e5d-859a265a1a3c', '9785fc531e2d3e27fb0f7ab230ca4ddaf055b77627ffa03697763cbf7b803444', 'ISSUE_DIPLOMA', 'success', 32, 418823, '2026-05-10 08:38:54'),
('64e2b450-b3d0-41b4-a9f2-1b88975d2e43', 'ecca4f20-59b4-4f45-834e-07fd1b010bff', NULL, 'ISSUE_DIPLOMA', 'pending', NULL, NULL, '2026-05-10 08:34:05');

-- --------------------------------------------------------

--
-- Table structure for table `universities`
--

CREATE TABLE `universities` (
  `id` char(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `accreditation` enum('A','B','C') DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `universities`
--

INSERT INTO `universities` (`id`, `name`, `accreditation`, `created_at`) VALUES
('310d497b-32c9-41c2-8fa2-416f2f8bfb35', 'Politeknik Negeri Padang', 'A', '2026-05-10 08:23:59');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` char(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `password_hash` text DEFAULT NULL,
  `role` enum('admin','university','validator') DEFAULT NULL,
  `university_id` char(36) DEFAULT NULL,
  `public_key` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `password_hash`, `role`, `university_id`, `public_key`, `created_at`) VALUES
('a2933f9e-5751-4a11-8a36-b2e42e464461', 'PNP', 'pnp@gmail.com', '$argon2id$v=19$m=65536,t=3,p=4$wjgHYCyFcK415pyTshYiJA$QrLyjdvF73GjRpiBs6PESZM0s+1BYNvKwwRI5mOzaVE', 'university', '310d497b-32c9-41c2-8fa2-416f2f8bfb35', '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoimja2h/+3vUC7kV7bIA\n9zxEspkr2Oc+YgsnHDJCGyWZoja3fyHVIHpgLob9NGhGr1TCWjvVxsS1rSFC23e1\nd305n0glLVKk7NhLHQ9MB64lhZpFirphOTbW5FIP+NOcbhKeI2BLwnvTBJanSgvQ\nDG5TNvJApVj5ibtavH9OH1y2yUVPCdLkEGlF4TpWF1EMadvLCkHnwVnF94bzpvLm\nGzuPbpv168dJAnUaOt0Twun3oN8xXWpmxJcHOld9Ty1miqz9O3C2PIWkwQngrta6\nnw3RIK6QsG4l3i6aGLRXQrs2n6wLPnLBBCH0wEA2RbIa5sSEQm7chbC0jX/CdsOa\nuQIDAQAB\n-----END PUBLIC KEY-----\n', '2026-05-10 08:25:01'),
('c85febf6-a4ad-47fe-ac1a-4d9db3d5c81c', 'Admin', 'admin@gmail.com', '$argon2id$v=19$m=65536,t=3,p=4$o9Q6x5hTao1xTmnN2ZtTag$i8F4xVp6GGeUvHsNOtHGHFR3KxKQ4QE/9ycYLNoQiBM', 'admin', NULL, NULL, '2026-05-10 08:22:51'),
('d624db50-9977-4d40-802b-48e3456478b1', 'Validator', 'validator@gmail.com', '$argon2id$v=19$m=65536,t=3,p=4$fs/5v9daS8k5J+SckzLGmA$NEJveDfE763NweRUwosR/ivqCljqp0ZxlMxR4L5+NZQ', 'validator', NULL, NULL, '2026-05-10 08:28:07');

-- --------------------------------------------------------

--
-- Table structure for table `wallets`
--

CREATE TABLE `wallets` (
  `id` char(36) NOT NULL,
  `student_id` char(36) DEFAULT NULL,
  `blockchain_address` varchar(255) DEFAULT NULL,
  `private_key_encrypted` text DEFAULT NULL,
  `is_connected` tinyint(1) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `wallets`
--

INSERT INTO `wallets` (`id`, `student_id`, `blockchain_address`, `private_key_encrypted`, `is_connected`, `created_at`) VALUES
('19599120-089a-4246-b868-7f5fc453dafc', 'bbcc3d5a-a5ce-443c-b20b-7c3d6cbcf39a', '0xDb25C1258Bb23E31Ec8B14024557887f50E768Fd', NULL, 1, '2026-05-10 08:27:39');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `diplomas`
--
ALTER TABLE `diplomas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `studies_id` (`studies_id`),
  ADD KEY `university_id` (`university_id`),
  ADD KEY `student_id` (`student_id`);

--
-- Indexes for table `students`
--
ALTER TABLE `students`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ktp_number` (`ktp_number`),
  ADD UNIQUE KEY `phone_number` (`phone_number`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `studies`
--
ALTER TABLE `studies`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nim` (`nim`),
  ADD KEY `student_id` (`student_id`),
  ADD KEY `university_id` (`university_id`);

--
-- Indexes for table `transactions`
--
ALTER TABLE `transactions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `tx_hash` (`tx_hash`);

--
-- Indexes for table `universities`
--
ALTER TABLE `universities`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `university_id` (`university_id`);

--
-- Indexes for table `wallets`
--
ALTER TABLE `wallets`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `student_id` (`student_id`),
  ADD UNIQUE KEY `blockchain_address` (`blockchain_address`);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `diplomas`
--
ALTER TABLE `diplomas`
  ADD CONSTRAINT `diplomas_ibfk_1` FOREIGN KEY (`studies_id`) REFERENCES `studies` (`id`),
  ADD CONSTRAINT `diplomas_ibfk_2` FOREIGN KEY (`university_id`) REFERENCES `universities` (`id`),
  ADD CONSTRAINT `diplomas_ibfk_3` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`);

--
-- Constraints for table `studies`
--
ALTER TABLE `studies`
  ADD CONSTRAINT `studies_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`),
  ADD CONSTRAINT `studies_ibfk_2` FOREIGN KEY (`university_id`) REFERENCES `universities` (`id`);

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`university_id`) REFERENCES `universities` (`id`);

--
-- Constraints for table `wallets`
--
ALTER TABLE `wallets`
  ADD CONSTRAINT `wallets_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
