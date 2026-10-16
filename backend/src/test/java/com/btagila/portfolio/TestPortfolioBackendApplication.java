package com.btagila.portfolio;

import org.springframework.boot.SpringApplication;

public class TestPortfolioBackendApplication {

	public static void main(String[] args) {
		SpringApplication.from(PortfolioBackendApplication::main).with(TestcontainersConfiguration.class).run(args);
	}

}
